import requests
from services.auth import get_token


BASE_URL = "http://localhost:8000"

def _auth_headers() -> dict:
    token = get_token()
    return {"Authorization": f"Bearer {token}"} if token else {}

def register(email: str, password: str, name: str) -> dict:
    resp = requests.post(f"{BASE_URL}/auth/register", json={
        "email": email, "password": password, "name": name
    })
    resp.raise_for_status()
    return resp.json()

def login(email: str, password: str) -> dict:
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": email, "password": password
    })
    resp.raise_for_status()
    return resp.json()

def get_topics() -> list:
    resp = requests.get(f"{BASE_URL}/topics")
    resp.raise_for_status()
    return resp.json()

def get_questions(topic_id: int) -> list:
    resp = requests.get(f"{BASE_URL}/topics/{topic_id}/questions")
    resp.raise_for_status()
    return resp.json()

def submit_evaluation(
    topic_id: int,
    question_text: str,
    answer_text: str,
    answer_mode: str,
    source: str,
    transcription_id: str | None = None,
) -> dict:
    resp = requests.post(
        f"{BASE_URL}/practice/evaluate",
        json={
            "topic_id": topic_id,
            "question_text": question_text,
            "answer_text": answer_text,
            "answer_mode": answer_mode,
            "source": source,
            "transcription_id": transcription_id,
        },
        headers=_auth_headers(),
    )
    resp.raise_for_status()
    return resp.json()


def transcribe_audio(audio_bytes: bytes, filename: str = "recording.wav") -> dict:
    files = {"audio": (filename, audio_bytes, "audio/wav")}
    resp = requests.post(
        f"{BASE_URL}/practice/transcribe",
        files=files,
        headers=_auth_headers(),
    )
    resp.raise_for_status()
    return resp.json()