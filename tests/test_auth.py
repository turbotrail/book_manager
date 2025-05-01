import pytest
from fastapi.testclient import TestClient
from app.api.routes.auth import router
from app.core.security import create_access_token

# Mock the create_access_token function
@pytest.fixture
def mock_create_access_token(monkeypatch):
    def mock_token(data):
        return "mocked_access_token"
    monkeypatch.setattr("app.core.security.create_access_token", mock_token)

# Create a TestClient for the router
client = TestClient(router)

def test_login_success(mock_create_access_token):
    response = client.post(
        "/token",
        data={"username": "admin", "password": "admin"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "access_token": "mocked_access_token",
        "token_type": "bearer"
    }

def test_login_invalid_credentials():
    response = client.post(
        "/token",
        data={"username": "wrong", "password": "credentials"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid credentials"}