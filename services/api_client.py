import requests

BASE_URL = "http://localhost:8000"

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