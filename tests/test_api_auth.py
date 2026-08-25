from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def _unique_email():
    import uuid
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


def test_register_and_login_flow():
    email = _unique_email()
    register_resp = client.post("/auth/register", json={
        "email": email, "password": "testpass123", "name": "Test User"
    })
    assert register_resp.status_code == 200
    assert "access_token" in register_resp.json()

    login_resp = client.post("/auth/login", json={
        "email": email, "password": "testpass123"
    })
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()


def test_duplicate_email_registration_fails():
    email = _unique_email()
    client.post("/auth/register", json={"email": email, "password": "pass123", "name": "A"})
    second_attempt = client.post("/auth/register", json={"email": email, "password": "pass456", "name": "B"})
    assert second_attempt.status_code == 400


def test_wrong_password_fails_login():
    email = _unique_email()
    client.post("/auth/register", json={"email": email, "password": "correctpass", "name": "A"})
    login_resp = client.post("/auth/login", json={"email": email, "password": "wrongpass"})
    assert login_resp.status_code == 401


def test_protected_endpoint_rejects_no_token():
    resp = client.get("/attempts")
    assert resp.status_code in (401, 403)  # FastAPI's HTTPBearer returns 403 if header missing entirely


def test_protected_endpoint_rejects_invalid_token():
    resp = client.get("/attempts", headers={"Authorization": "Bearer not.a.real.token"})
    assert resp.status_code == 401