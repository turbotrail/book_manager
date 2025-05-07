import pytest
from httpx import AsyncClient
from app.main import app
from app.db.database import get_db, SessionLocal
from app.db.models import User
from app.core.security import hash_password
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

@pytest.fixture
async def test_user(db_session: AsyncSession):
    user = User(username="admin", password=hash_password("admin"))
    db_session.add(user)
    await db_session.commit()
    return user

@pytest.mark.anyio
async def test_login_success(test_user):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/auth/token",
            data={"username": "admin", "password": "admin"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

@pytest.mark.anyio
async def test_login_invalid_username():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/auth/token",
            data={"username": "wrong", "password": "admin"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid credentials"}

@pytest.mark.anyio
async def test_login_invalid_password(test_user):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/auth/token",
            data={"username": "admin", "password": "wrongpass"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid credentials"}

@pytest.mark.anyio
async def test_register_success():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/auth/register",
            data={"username": "newuser", "password": "newpass"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
    assert response.status_code == 200
    assert "User registered successfully" in response.json()["message"]

@pytest.mark.anyio
async def test_register_existing_user(test_user):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/auth/register",
            data={"username": "admin", "password": "admin"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already taken"}
async def override_get_db():
    async with SessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db