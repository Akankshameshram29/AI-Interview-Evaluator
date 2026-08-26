import requests
from services.auth import get_token

BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT = 30  # seconds


def _auth_headers() -> dict:
    token = get_token()
    return {"Authorization": f"Bearer {token}"} if token else {}


def register(email: str, password: str, name: str) -> dict:
    resp = requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": email, "password": password, "name": name},
        timeout=DEFAULT_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def login(email: str, password: str) -> dict:
    """Attempts login using JSON payload first, falling back to OAuth2 Form Data if required."""
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": email, "password": password},
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        # Fallback for FastAPI OAuth2PasswordRequestForm standard endpoints
        if e.response.status_code in (400, 422):
            resp = requests.post(
                f"{BASE_URL}/auth/login",
                data={"username": email, "password": password},
                timeout=DEFAULT_TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()
        raise e


def get_topics() -> list:
    resp = requests.get(f"{BASE_URL}/topics", timeout=DEFAULT_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_questions(topic_id: int) -> list:
    resp = requests.get(f"{BASE_URL}/topics/{topic_id}/questions", timeout=DEFAULT_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def submit_evaluation(
    topic_id: int,
    question_text: str,
    answer_text: str,
    answer_mode: str,
    source: str,
    transcription_id: int | str | None = None,
) -> dict:
    payload = {
        "topic_id": topic_id,
        "question_text": question_text,
        "answer_text": answer_text,
        "answer_mode": answer_mode,
        "source": source,
        "transcription_id": transcription_id,
    }
    
    resp = requests.post(
        f"{BASE_URL}/practice/evaluate",
        json=payload,
        headers=_auth_headers(),
        timeout=60,  # Higher timeout for LLM evaluation requests
    )
    resp.raise_for_status()
    return resp.json()


def transcribe_audio(audio_bytes: bytes, filename: str = "recording.wav") -> dict:
    files = {"audio": (filename, audio_bytes, "audio/wav")}
    resp = requests.post(
        f"{BASE_URL}/practice/transcribe",
        files=files,
        headers=_auth_headers(),
        timeout=60,  # Higher timeout for audio transcription requests
    )
    resp.raise_for_status()
    return resp.json()


def get_attempts() -> list:
    resp = requests.get(
        f"{BASE_URL}/attempts",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def get_attempt_detail(attempt_id: int) -> dict:
    resp = requests.get(
        f"{BASE_URL}/attempts/{attempt_id}",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def get_progress() -> list:
    resp = requests.get(
        f"{BASE_URL}/progress",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()