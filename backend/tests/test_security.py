import jwt

from app.security import hash_password, verify_password
from tests.conftest import make_client, signup, stream_review


def test_idor_user_cannot_read_another_users_review():
    c = make_client()
    alice, bob = signup(c, "alice@example.com"), signup(c, "bob@example.com")
    _, events = stream_review(c, alice, title="alice secret")
    review_id = events[0][1]["id"]

    assert c.get(f"/api/reviews/{review_id}", headers=alice).status_code == 200
    resp = c.get(f"/api/reviews/{review_id}", headers=bob)
    assert resp.status_code == 404  # same answer as a non-existent id
    assert "alice" not in resp.text
    assert c.get("/api/reviews", headers=bob).json() == []
    assert c.get("/api/reviews/99999", headers=bob).status_code == 404


def test_forged_tokens_rejected():
    c = make_client()
    signup(c)
    forged = jwt.encode({"sub": "1"}, "wrong-secret-wrong-secret-wrong-1234", algorithm="HS256")
    assert c.get("/api/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401
    unsigned = jwt.encode({"sub": "1"}, None, algorithm="none")
    assert c.get("/api/auth/me", headers={"Authorization": f"Bearer {unsigned}"}).status_code == 401


def test_password_is_hashed():
    h = hash_password("password123")
    assert "password123" not in h
    assert verify_password("password123", h) and not verify_password("other", h)
