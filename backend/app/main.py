from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.database import Base, make_engine, make_session_factory
from app.gateway.limits import RateLimiter
from app.llm import build_provider
from app.routers import auth, billing, reviews
from app.services.billing import FakePaymentProvider
from app.services.cache import MemoryCache


def create_app(settings: Settings | None = None, provider=None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="review-desk", version="1.0.0")

    engine = make_engine(settings.database_url)
    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(engine)  # dev/test convenience; Postgres uses Alembic
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = make_session_factory(engine)
    app.state.provider = provider or build_provider(settings)
    app.state.cache = MemoryCache()
    app.state.rate_limiter = RateLimiter(settings.rate_limit_per_minute)
    app.state.auth_limiter = RateLimiter(30)
    app.state.payments = FakePaymentProvider()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth.router)
    app.include_router(reviews.router)
    app.include_router(billing.router)

    @app.get("/api/health")
    def health():
        return {"status": "ok", "llm_provider": app.state.provider.name}

    return app
