from tests.conftest import signup


def test_signup_login_me(client):
    headers = signup(client, "x@example.com")
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "x@example.com"
    assert me.json()["plan"] == "free"
    creds = {"email": "x@example.com", "password": "password123"}
    assert client.post("/api/auth/login", json=creds).status_code == 200


def test_duplicate_email_conflict(client):
    signup(client, "dup@example.com")
    r = client.post(
        "/api/auth/signup", json={"email": "DUP@example.com", "password": "password123"}
    )
    assert r.status_code == 409


def test_wrong_password_and_validation(client):
    signup(client, "w@example.com")
    bad = client.post("/api/auth/login", json={"email": "w@example.com", "password": "nope-nope-1"})
    assert bad.status_code == 401
    short = client.post("/api/auth/signup", json={"email": "s@example.com", "password": "short"})
    assert short.status_code == 422


def test_protected_routes_require_token(client):
    assert client.get("/api/reviews").status_code == 401
    assert client.get("/api/usage").status_code == 401
    bad = client.get("/api/reviews", headers={"Authorization": "Bearer not-a-jwt"})
    assert bad.status_code == 401
