import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.gateway.deps import current_user, get_db
from app.gateway.limits import enforce_quota, enforce_size
from app.llm.base import ProviderError
from app.models import Finding, Review, User, utcnow
from app.schemas import ReviewDetail, ReviewIn, ReviewSummary
from app.services import billing
from app.services.agent import run_review

router = APIRouter(prefix="/api/reviews", tags=["reviews"])
log = logging.getLogger("review_desk")


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.get("", response_model=list[ReviewSummary])
def list_reviews(user: User = Depends(current_user), db: Session = Depends(get_db)):
    counts = (
        select(Finding.review_id, func.count(Finding.id).label("n"))
        .group_by(Finding.review_id)
        .subquery()
    )
    rows = db.execute(
        select(Review, func.coalesce(counts.c.n, 0))
        .outerjoin(counts, counts.c.review_id == Review.id)
        .where(Review.user_id == user.id)
        .order_by(Review.created_at.desc(), Review.id.desc())
        .limit(100)
    ).all()
    return [
        ReviewSummary(
            id=r.id,
            title=r.title,
            language=r.language,
            status=r.status,
            created_at=r.created_at,
            finding_count=n,
        )
        for r, n in rows
    ]


@router.get("/{review_id}", response_model=ReviewDetail)
def get_review(review_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    review = db.scalar(select(Review).where(Review.id == review_id, Review.user_id == user.id))
    if review is None:  # same 404 for "missing" and "not yours": no existence leak
        raise HTTPException(status_code=404, detail="Review not found")
    return review


@router.post("/stream")
async def stream_review(
    body: ReviewIn,
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    state = request.app.state
    # --- gateway checks: all before any LLM call ---------------------------------------------
    state.rate_limiter.check(f"user:{user.id}")
    enforce_size(body.code, state.settings.max_code_chars)
    plan = billing.get_plan(user.plan)
    used = billing.used_this_period(db, state.cache, user.id, use_cache=False)
    enforce_quota(used, plan.monthly_reviews, plan.id)

    review = Review(
        user_id=user.id,
        title=body.title.strip() or "Untitled review",
        language=body.language,
        code=body.code,
        provider=state.provider.name,
    )
    db.add(review)
    db.flush()
    billing.record_usage(db, state.cache, user.id, review.id, len(body.code))
    db.commit()
    review_id = review.id

    async def events() -> AsyncIterator[str]:
        completed = False
        with state.session_factory() as session:
            try:
                yield _sse("review", {"id": review_id})
                async for ev in run_review(state.provider, body.code, body.language):
                    if ev.type == "final":
                        row = session.get(Review, review_id)
                        row.findings = [
                            Finding(position=i, **f) for i, f in enumerate(ev.data["findings"])
                        ]
                        row.summary = ev.data["summary"]
                        row.status = "done"
                        row.completed_at = utcnow()
                        session.commit()
                        completed = True
                    yield _sse(ev.type, ev.data)
                yield _sse("done", {"id": review_id})
            except ProviderError as exc:
                yield _sse("error", {"message": str(exc)})
            except Exception:  # noqa: BLE001 - never leak internals to the client
                log.exception("review %s failed", review_id)
                yield _sse("error", {"message": "Internal error while reviewing."})
            finally:
                if not completed:  # failed or client disconnected: mark failed, don't bill
                    session.rollback()
                    row = session.get(Review, review_id)
                    if row is not None:
                        row.status = "failed"
                    billing.refund_usage(session, state.cache, review_id)
                    session.commit()

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
