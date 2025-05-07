import pytest
from httpx import AsyncClient
from fastapi import status
from app.main import app
from app.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.db import models

# Mock database setup
DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(DATABASE_URL, future=True, echo=True)
TestingSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)

@pytest.fixture
async def client():
    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def create_user(client):
    async def _create_user(username, preferences=None):
        async with TestingSessionLocal() as db:
            user = models.User(username=username, **(preferences or {}))
            db.add(user)
            await db.commit()
    return _create_user

@pytest.mark.asyncio
async def test_save_preferences(client):
    async with client as ac:
        payload = {
            "genre": "Science Fiction",
            "author": "Isaac Asimov",
            "min_year": 1950,
            "max_year": 2000
        }
        response = await ac.post("/preferences", json=payload)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"message": "Preferences saved successfully"}

@pytest.mark.asyncio
async def test_get_recommendations_no_preferences(client):
    async with client as ac:
        response = await ac.get("/recommendations")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {"detail": "No preferences found for user"}

@pytest.mark.asyncio
async def test_get_recommendations_with_preferences(client, create_user):
    await create_user("test_user", {
        "genre": "Fantasy",
        "author": "J.K. Rowling",
        "min_year": 1990,
        "max_year": 2020
    })

    # Add mock books to the database
    async with TestingSessionLocal() as db:
        books = [
            models.Book(
                title="Harry Potter and the Philosopher's Stone",
                author="J.K. Rowling",
                genre="Fantasy",
                year_published=1997,
                summary="A young wizard's journey begins."
            ),
            models.Book(
                title="The Hobbit",
                author="J.R.R. Tolkien",
                genre="Fantasy",
                year_published=1937,
                summary="A hobbit's adventure to reclaim a lost treasure."
            )
        ]
        db.add_all(books)
        await db.commit()

    async with client as ac:
        response = await ac.get("/recommendations")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "recommendation_summary" in data
        assert len(data["books"]) > 0