import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.database import get_db, Base
from app.db.models import User
from app.core.security import hash_password
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.future import select
import asyncio
import time

TEST_DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/booksdb"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)

@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    retries = 5
    for i in range(retries):
        try:
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                await conn.run_sync(Base.metadata.create_all)
            break
        except Exception as e:
            if i < retries - 1:
                print(f"DB not ready yet ({i+1}/{retries}) — retrying...")
                time.sleep(3)
            else:
                raise e
    app.dependency_overrides[get_db] = override_get_db

async def override_get_db():
    async with TestSessionLocal() as session:
        yield session

@pytest.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session

@pytest.fixture
async def test_user(db_session: AsyncSession):
    user = User(username="admin", password=hash_password("admin"))
    db_session.add(user)
    await db_session.commit()
    return user

@pytest.mark.anyio("asyncio")
async def test_login_success(test_user):
    transport = ASGITransport(app=app, root_path="")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/auth/token",
            data={"username": "admin", "password": "admin"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

@pytest.mark.anyio("asyncio")
async def test_login_invalid_username():
    transport = ASGITransport(app=app, root_path="")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/auth/token",
            data={"username": "wrong", "password": "admin"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid credentials"}

@pytest.mark.anyio("asyncio")
async def test_login_invalid_password(test_user):
    transport = ASGITransport(app=app, root_path="")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/auth/token",
            data={"username": "admin", "password": "wrongpass"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid credentials"}

@pytest.mark.anyio("asyncio")
async def test_register_success():
    transport = ASGITransport(app=app, root_path="")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/auth/register",
            data={"username": "newuser", "password": "newpass"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
    assert response.status_code == 200
    assert "User registered successfully" in response.json()["message"]

@pytest.mark.anyio("asyncio")
async def test_register_existing_user(test_user):
    transport = ASGITransport(app=app, root_path="")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/auth/register",
            data={"username": "admin", "password": "admin"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already taken"}