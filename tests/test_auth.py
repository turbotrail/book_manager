from app.main import app
from app.db.database import get_db

from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

app.router.on_startup.clear()

def override_get_db_with_user(user_exists=True, password_valid=True):
    async def _override():
        mock_user = MagicMock() if user_exists else None
        if mock_user:
            mock_user.username = "mockuser"
            mock_user.password = "hashed"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user

        mock_session = MagicMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        yield mock_session
    return _override  # fix: return the function, not the generator

client_sync = TestClient(app)

@patch("app.main.init_db", new_callable=AsyncMock)
@patch("app.api.routes.auth.verify_password")
@patch("app.api.routes.auth.create_access_token", return_value="mockedtoken")
def test_login_unit_success(mock_token, mock_verify, mock_init_db):
    app.dependency_overrides[get_db] = override_get_db_with_user()
    mock_verify.return_value = True

    response = client_sync.post("/auth/token", data={"username": "mockuser", "password": "mockpass"})
    assert response.status_code == 200
    assert response.json()["access_token"] == "mockedtoken"

@patch("app.main.init_db", new_callable=AsyncMock)
@patch("app.api.routes.auth.verify_password")
def test_login_unit_fail(mock_verify, mock_init_db):
    app.dependency_overrides[get_db] = override_get_db_with_user(password_valid=False)
    mock_verify.return_value = False

    response = client_sync.post("/auth/token", data={"username": "mockuser", "password": "wrong"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid credentials"}

@patch("app.main.init_db", new_callable=AsyncMock)
@patch("app.api.routes.auth.hash_password", return_value="hashed")
def test_register_unit_success(mock_hash, mock_init_db):
    app.dependency_overrides[get_db] = override_get_db_with_user(user_exists=False)

    response = client_sync.post("/auth/register", data={"username": "newuser", "password": "newpass"})
    assert response.status_code == 200
    assert "User registered successfully" in response.json()["message"]

@patch("app.main.init_db", new_callable=AsyncMock)
def test_register_unit_existing_user(mock_init_db):
    app.dependency_overrides[get_db] = override_get_db_with_user()

    response = client_sync.post("/auth/register", data={"username": "existing", "password": "any"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already taken"}