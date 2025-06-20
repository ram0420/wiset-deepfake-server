# tests/test_auth.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_and_login():
    # 회원가입
    response = client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "password": "testpassword",
        "email": "test@example.com",
        "school": "Test School",
        "grade": 1,
        "classNumber": 1
    })
    assert response.status_code == 201
    user_id = response.json()["userId"]

    # 로그인
    login_response = client.post("/api/v1/auth/login", json={
        "username": "test@example.com",  # 여기 이메일로 로그인한다고 가정
        "password": "testpassword"
    })
    assert login_response.status_code == 200
    data = login_response.json()
    assert "token" in data
    assert data["userId"] == user_id
