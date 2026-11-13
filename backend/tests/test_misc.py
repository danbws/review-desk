import asyncio
import os
import subprocess
import sys

from app.config import Settings
from app.llm import build_provider
from app.llm.fake import FakeProvider
from app.services.cache import MemoryCache


def test_provider_selection():
    assert build_provider(Settings(llm_provider="auto", anthropic_api_key="")).name == "fake"
    keyed = Settings(llm_provider="auto", anthropic_api_key="sk-test")
    assert build_provider(keyed).name == "anthropic"


def test_fake_provider_is_deterministic():
    async def collect():
        p = FakeProvider()
        user = "<code>\n1: eval(x)\n</code>"
        return "".join([c async for c in p.stream(system="", user=user, purpose="review")])

    assert asyncio.run(collect()) == asyncio.run(collect())


def test_cache_ttl():
    c = MemoryCache()
    c.set("k", 1, ttl=-1)
    assert c.get("k") is None
    c.set("k", 2, ttl=10)
    assert c.get("k") == 2


def test_alembic_migration_matches_models(tmp_path):
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{tmp_path / 'm.db'}"}
    for cmd in ("upgrade head", "check"):
        run = subprocess.run(
            [sys.executable, "-m", "alembic", *cmd.split()], env=env, capture_output=True, text=True
        )
        assert run.returncode == 0, run.stdout + run.stderr


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok", "llm_provider": "fake"}
