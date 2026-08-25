from fastapi.testclient import TestClient
from backend.main import app
import uuid

client = TestClient(app)


def _register_and_login():
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/auth/register", json={"email": email, "password": "pass1234", "name": "Test"})
    login_resp = client.post("/auth/login", json={"email": email, "password": "pass1234"})
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_user_cannot_view_another_users_attempt():
    headers_a = _register_and_login()
    headers_b = _register_and_login()

    # User A submits an attempt
    topics_resp = client.get("/topics")
    topic_id = topics_resp.json()[0]["id"]

    evaluate_resp = client.post(
        "/practice/evaluate",
        json={
            "topic_id": topic_id,
            "question_text": "Test question for isolation check",
            "answer_text": "Test answer text for isolation check",
            "answer_mode": "text",
            "source": "custom",
        },
        headers=headers_a,
    )
    assert evaluate_resp.status_code == 200
    attempt_id = evaluate_resp.json()["attempt_id"]

    # User B tries to view User A's attempt directly
    detail_resp = client.get(f"/attempts/{attempt_id}", headers=headers_b)
    assert detail_resp.status_code == 404  # not found, not "here's someone else's data"


def test_user_only_sees_own_attempts_in_list():
    headers_a = _register_and_login()
    headers_b = _register_and_login()

    topic_id = client.get("/topics").json()[0]["id"]

    client.post("/practice/evaluate", json={
        "topic_id": topic_id, "question_text": "A's question", "answer_text": "A's answer",
        "answer_mode": "text", "source": "custom",
    }, headers=headers_a)

    b_attempts = client.get("/attempts", headers=headers_b).json()
    assert all("A's question" != a["question_text"] for a in b_attempts)