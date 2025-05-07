import pytest
from httpx import AsyncClient
from fastapi import status
from app.main import app
from app.db import models
from app.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

# Mock database setup
DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(DATABASE_URL, future=True, echo=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

@pytest.fixture
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)

@pytest.fixture
async def client(db_session):
    async def override_get_db():
        async for session in db_session:
            yield session
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac

@pytest.mark.asyncio
async def test_register_user(client):
    async with client as ac:
        response = await ac.post(
            "/register",
            data={"username": "testuser", "password": "testpassword"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"message": "User registered successfully testuser"}

@pytest.mark.asyncio
async def test_register_existing_user(client, db_session):
    async with db_session as session:
        hashed_password = "hashedpassword"
        new_user = models.User(username="testuser", password=hashed_password)
        session.add(new_user)
        await session.commit()

    async with client as ac:
        response = await ac.post(
            "/register",
            data={"username": "testuser", "password": "testpassword"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"detail": "Username already taken"}

@pytest.mark.asyncio
async def test_login_user(client, db_session):
    async with db_session as session:
        hashed_password = "hashedpassword"
        new_user = models.User(username="testuser", password=hashed_password)
        session.add(new_user)
        await session.commit()

    async def mock_verify_password(plain_password, hashed_password):
        return True

    app.dependency_overrides[verify_password] = mock_verify_password

    async with client as ac:
        response = await ac.post(
            "/token",
            data={"username": "testuser", "password": "testpassword"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    async with client as ac:
        response = await ac.post(
            "/token",
            data={"username": "invaliduser", "password": "invalidpassword"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"detail": "Invalid credentials"}

@pytest.mark.asyncio
async def test_register_user_with_empty_password(client):
    response = await client.post(
        "/register",
        data={"username": "testuser2", "password": ""}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio
async def test_login_user_with_empty_username(client):
    response = await client.post(
        "/token",
        data={"username": "", "password": "testpassword"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac

@pytest.mark.asyncio
async def test_register_user(client):
    response = await client.post(
        "/register",
        data={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "User registered successfully testuser"}

@pytest.mark.asyncio
async def test_register_existing_user(client, db_session):
    # Create a user in the database
    hashed_password = "hashedpassword"
    new_user = models.User(username="testuser", password=hashed_password)
    db_session.add(new_user)
    await db_session.commit()

    # Try to register the same user again
    response = await client.post(
        "/register",
        data={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Username already taken"}

@pytest.mark.asyncio
async def test_login_user(client, db_session):
    # Create a user in the database
    hashed_password = "hashedpassword"
    new_user = models.User(username="testuser", password=hashed_password)
    db_session.add(new_user)
    await db_session.commit()

    # Mock verify_password to return True
    async def mock_verify_password(plain_password, hashed_password):
        return True

    app.dependency_overrides[verify_password] = mock_verify_password

    response = await client.post(
        "/token",
        data={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    response = await client.post(
        "/token",
        data={"username": "invaliduser", "password": "invalidpassword"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Invalid credentials"}