"""Create a demo user with two sample reviews: python -m app.seed"""

import asyncio

from sqlalchemy import select

from app.config import get_settings
from app.database import make_engine, make_session_factory
from app.llm import build_provider
from app.models import Finding, Review, User, utcnow
from app.security import hash_password
from app.services import billing
from app.services.agent import run_review
from app.services.cache import MemoryCache

DEMO_EMAIL = "demo@reviewdesk.dev"
DEMO_PASSWORD = "demo-password"  # demo data only

SAMPLES = [
    (
        "Login handler",
        "python",
        'import sqlite3\n\npassword = "hunter2"  # TODO: move to env\n\n'
        "def find_user(db, name):\n"
        '    q = "SELECT * FROM users WHERE name = \'" + name + "\'"\n'
        "    try:\n        return db.execute(q).fetchone()\n"
        "    except:\n        print('failed')\n",
    ),
    (
        "Calculator eval",
        "python",
        "def calc(expr):\n    return eval(expr)\n",
    ),
]


async def _review(provider, code: str, language: str) -> dict:
    final: dict = {}
    async for ev in run_review(provider, code, language):
        if ev.type == "final":
            final = ev.data
    return final


def main() -> None:
    settings = get_settings()
    engine = make_engine(settings.database_url)
    factory = make_session_factory(engine)
    provider = build_provider(settings)
    cache = MemoryCache()
    with factory() as db:
        user = db.scalar(select(User).where(User.email == DEMO_EMAIL))
        if user is None:
            user = User(email=DEMO_EMAIL, password_hash=hash_password(DEMO_PASSWORD))
            db.add(user)
            db.flush()
        if db.scalar(select(Review).where(Review.user_id == user.id)):
            print("Demo data already present.")
            return
        for title, lang, code in SAMPLES:
            result = asyncio.run(_review(provider, code, lang))
            review = Review(
                user_id=user.id,
                title=title,
                language=lang,
                code=code,
                status="done",
                provider=provider.name,
                summary=result["summary"],
                completed_at=utcnow(),
                findings=[Finding(position=i, **f) for i, f in enumerate(result["findings"])],
            )
            db.add(review)
            db.flush()
            billing.record_usage(db, cache, user.id, review.id, len(code))
        db.commit()
    print(f"Seeded {DEMO_EMAIL} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
