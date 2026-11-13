from tests.conftest import make_client, signup, stream_review


def test_free_plan_quota_returns_402(client, auth):
    for _ in range(5):
        assert stream_review(client, auth)[0] == 200
    usage = client.get("/api/usage", headers=auth).json()
    assert (usage["used"], usage["limit"], usage["remaining"]) == (5, 5, 0)
    r = client.post("/api/reviews/stream", headers=auth, json={"code": "x = 1"})
    assert r.status_code == 402 and "Upgrade" in r.json()["detail"]


def test_upgrade_to_pro_lifts_the_limit(client, auth):
    for _ in range(5):
        stream_review(client, auth)
    assert stream_review(client, auth)[0] == 402
    up = client.post("/api/billing/checkout", headers=auth, json={"plan": "pro"})
    assert up.status_code == 200 and up.json()["provider"] == "fake"
    assert stream_review(client, auth)[0] == 200
    assert client.get("/api/usage", headers=auth).json()["limit"] == 200


def test_quota_is_per_user():
    c = make_client()
    a, b = signup(c, "a@example.com"), signup(c, "b@example.com")
    for _ in range(5):
        stream_review(c, a)
    assert stream_review(c, a)[0] == 402
    assert stream_review(c, b)[0] == 200


def test_rate_limit_returns_429_with_retry_after():
    c = make_client(rate_limit_per_minute=2)
    h = signup(c)
    assert stream_review(c, h)[0] == 200
    assert stream_review(c, h)[0] == 200
    r = c.post("/api/reviews/stream", headers=h, json={"code": "x = 1"})
    assert r.status_code == 429
    assert int(r.headers["retry-after"]) >= 1


def test_oversized_input_is_rejected_413_and_not_billed():
    c = make_client(max_code_chars=50)
    h = signup(c)
    assert stream_review(c, h, code="x" * 51)[0] == 413
    assert c.get("/api/usage", headers=h).json()["used"] == 0


def test_unknown_plan_rejected(client, auth):
    r = client.post("/api/billing/checkout", headers=auth, json={"plan": "enterprise"})
    assert r.status_code == 422
