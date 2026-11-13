import json

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def make_client(**overrides) -> TestClient:
    params = {
        "database_url": "sqlite://",
        "llm_provider": "fake",
        "jwt_secret": "test-secret-test-secret-test-secret-0123",
        "rate_limit_per_minute": 1000,
        **overrides,
    }
    return TestClient(create_app(Settings(**params)))


@pytest.fixture
def client() -> TestClient:
    return make_client()


def signup(client: TestClient, email: str = "a@example.com", password: str = "password123") -> dict:
    r = client.post("/api/auth/signup", json={"email": email, "password": password})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def auth(client) -> dict:
    return signup(client)


SAMPLE = 'password = "hunter2"\nresult = eval(user_input)\n'


def stream_review(client: TestClient, headers: dict, code: str = SAMPLE, **extra):
    """POST /stream and return (status_code, events) where events is [(name, data)]."""
    events: list[tuple[str, dict]] = []
    with client.stream(
        "POST", "/api/reviews/stream", headers=headers, json={"code": code, **extra}
    ) as r:
        if r.status_code != 200:
            r.read()
            return r.status_code, events
        name = None
        for line in r.iter_lines():
            if line.startswith("event: "):
                name = line[7:]
            elif line.startswith("data: "):
                events.append((name, json.loads(line[6:])))
    return 200, events
