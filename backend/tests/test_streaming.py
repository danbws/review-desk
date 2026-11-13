from fastapi.testclient import TestClient

from app.config import Settings
from app.llm.base import ProviderError
from app.main import create_app
from tests.conftest import signup, stream_review


def test_sse_stream_with_fake_provider(client, auth):
    status, events = stream_review(client, auth, title="t1", language="python")
    assert status == 200
    names = [n for n, _ in events]
    assert names[0] == "review" and names[-1] == "done"
    assert names.count("token") > 3
    assert ("pass", {"name": "verify"}) in events  # the agent called itself again
    drafts = [d for n, d in events if n == "draft"]
    final = next(d for n, d in events if n == "final")
    assert len(drafts) == 3  # eval + credential + intentional duplicate
    assert len(final["findings"]) == 2  # verify pass removed the duplicate
    assert final["findings"][0]["severity"] == "critical"  # sorted by severity
    assert final["findings"][0]["line"] == 2


def test_review_is_persisted_and_listed(client, auth):
    _, events = stream_review(client, auth, title="Persist me")
    review_id = events[0][1]["id"]
    detail = client.get(f"/api/reviews/{review_id}", headers=auth).json()
    assert detail["status"] == "done"
    assert detail["title"] == "Persist me"
    assert len(detail["findings"]) == 2
    listing = client.get("/api/reviews", headers=auth).json()
    assert listing[0]["id"] == review_id and listing[0]["finding_count"] == 2


def test_provider_failure_marks_failed_and_refunds():
    class Boom:
        name = "boom"

        async def stream(self, **kwargs):
            raise ProviderError("provider is down")
            yield ""  # pragma: no cover

    app = create_app(Settings(database_url="sqlite://", jwt_secret="t" * 32), provider=Boom())
    c = TestClient(app)
    headers = signup(c, "boom@example.com")
    _, events = stream_review(c, headers)
    assert events[-1] == ("error", {"message": "provider is down"})
    assert c.get("/api/usage", headers=headers).json()["used"] == 0  # not billed
    assert c.get("/api/reviews", headers=headers).json()[0]["status"] == "failed"
