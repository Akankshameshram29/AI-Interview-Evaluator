from fastapi.testclient import TestClient
from backend.main import app
import uuid

client = TestClient(app)


def _register_and_login():
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/auth/register", json={"email": email, "password": "pass1234", "name": "Test"})
    return {"Authorization": f"Bearer {client.post('/auth/login', json={'email': email, 'password': 'pass1234'}).json()['access_token']}"}


def test_custom_question_not_in_database_still_evaluates():
    headers = _register_and_login()
    topic_id = client.get("/topics").json()[0]["id"]

    resp = client.post("/practice/evaluate", json={
        "topic_id": topic_id,
        "question_text": "This is a totally made-up question that definitely is not seeded in the database",
        "answer_text": "Some reasonable answer text explaining a concept.",
        "answer_mode": "text",
        "source": "custom",
    }, headers=headers)

    assert resp.status_code == 200
    body = resp.json()
    # A rubric was generated for this novel question — proven by non-empty concept_results
    assert "concept_results" in body["feedback"]
    assert len(body["feedback"]["concept_results"]) > 0