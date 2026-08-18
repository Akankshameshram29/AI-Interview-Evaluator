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