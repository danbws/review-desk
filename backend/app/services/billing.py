"""Billing service: plans, usage metering and a payment-provider interface.

No real payment integration exists in this project. `FakePaymentProvider` upgrades the plan
immediately and returns a fake URL; a Stripe implementation would implement `PaymentProvider`
(create a Checkout Session, activate the plan from a signed webhook) and nothing else changes.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import UsageEvent, User
from app.services.cache import Cache


@dataclass(frozen=True)
class Plan:
    id: str
    name: str
    monthly_reviews: int
    price_usd_month: int


PLANS: dict[str, Plan] = {
    "free": Plan("free", "Free", 5, 0),
    "pro": Plan("pro", "Pro", 200, 19),
}


def get_plan(plan_id: str) -> Plan:
    return PLANS.get(plan_id, PLANS["free"])


def current_period(now: datetime | None = None) -> str:
    return (now or datetime.now(UTC)).strftime("%Y-%m")


def _usage_key(user_id: int, period: str) -> str:
    return f"usage:{user_id}:{period}"


def used_this_period(
    db: Session, cache: Cache, user_id: int, period: str | None = None, use_cache: bool = True
) -> int:
    """Quota enforcement passes use_cache=False; the cache only serves the dashboard."""
    period = period or current_period()
    cached = cache.get(_usage_key(user_id, period)) if use_cache else None
    if cached is not None:
        return cached
    used = db.scalar(
        select(func.count(UsageEvent.id)).where(
            UsageEvent.user_id == user_id, UsageEvent.period == period
        )
    )
    cache.set(_usage_key(user_id, period), used or 0, ttl=15)
    return used or 0


def usage_summary(db: Session, cache: Cache, user: User) -> dict:
    plan = get_plan(user.plan)
    period = current_period()
    used = used_this_period(db, cache, user.id, period)
    return {
        "plan": plan.id,
        "period": period,
        "used": used,
        "limit": plan.monthly_reviews,
        "remaining": max(plan.monthly_reviews - used, 0),
    }


def record_usage(db: Session, cache: Cache, user_id: int, review_id: int, chars: int) -> None:
    period = current_period()
    db.add(UsageEvent(user_id=user_id, review_id=review_id, period=period, chars=chars))
    cache.delete(_usage_key(user_id, period))


def refund_usage(db: Session, cache: Cache, review_id: int) -> None:
    for event in db.scalars(select(UsageEvent).where(UsageEvent.review_id == review_id)):
        cache.delete(_usage_key(event.user_id, event.period))
        db.delete(event)


class PaymentProvider(Protocol):
    name: str

    def start_checkout(self, user: User, plan: Plan) -> dict:
        """Return {"status": "active"|"pending", "checkout_url": str | None}."""
        ...


class FakePaymentProvider:
    name = "fake"

    def start_checkout(self, user: User, plan: Plan) -> dict:
        return {"status": "active", "checkout_url": None}


def change_plan(db: Session, provider: PaymentProvider, user: User, plan_id: str) -> dict:
    plan = PLANS[plan_id]
    result = provider.start_checkout(user, plan)
    if result["status"] == "active":
        user.plan = plan.id
        db.commit()
    return result
