import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.db import models

# Mock database setup
DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(DATABASE_URL, echo=True)
TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)

@pytest.fixture(scope="module")
async def test_db():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        yield session
    await engine.dispose()

@pytest.fixture(scope="module")
async def client(test_db: AsyncSession):
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def create_user(test_db: AsyncSession):
    user = models.User(username="testuser", genre="Fantasy", author="Tolkien", min_year=1950, max_year=2000)
    test_db.add(user)
    await test_db.commit()
    return user

@pytest.fixture
async def create_books(test_db: AsyncSession):
    books = [
        models.Book(title="The Hobbit", author="J.R.R. Tolkien", genre="Fantasy", year_published=1937, summary="A hobbit's adventure."),
        models.Book(title="The Fellowship of the Ring", author="J.R.R. Tolkien", genre="Fantasy", year_published=1954, summary="The first part of the epic journey."),
        models.Book(title="1984", author="George Orwell", genre="Dystopian", year_published=1949, summary="A dystopian novel."),
    ]
    test_db.add_all(books)
    await test_db.commit()
    return books

@pytest.mark.asyncio
async def test_save_preferences(client: AsyncClient):
    response = await client.post(
        "/preferences",
        json={
            "genre": "Science Fiction",
            "author": "Isaac Asimov",
            "min_year": 1950,
            "max_year": 2000,
        },
        headers={"Authorization": "Bearer testuser"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Preferences saved successfully"}

@pytest.mark.asyncio
async def test_get_recommendations_no_preferences(client: AsyncClient):
    response = await client.get("/recommendations", headers={"Authorization": "Bearer unknownuser"})
    assert response.status_code == 404
    assert response.json() == {"detail": "No preferences found for user"}

@pytest.mark.asyncio
async def test_get_recommendations_with_matches(client: AsyncClient, create_user, create_books):
    response = await client.get("/recommendations", headers={"Authorization": "Bearer testuser"})
    assert response.status_code == 200
    data = response.json()
    assert "recommendation_summary" in data
    assert len(data["books"]) > 0
    assert any(book["title"] == "The Fellowship of the Ring" for book in data["books"])

@pytest.mark.asyncio
async def test_get_recommendations_no_matches(client: AsyncClient, create_user, test_db):
    # Clear books to ensure no matches
    await test_db.execute("DELETE FROM books")
    await test_db.commit()

    response = await client.get("/recommendations", headers={"Authorization": "Bearer testuser"})
    assert response.status_code == 200
    assert response.json() == {"message": "Sorry, we couldn't find any books matching your preferences."}


# Moved nested test functions out as top-level functions:

@pytest.mark.asyncio
async def test_save_preferences_overwrite(client: AsyncClient, create_user):
    response = await client.post(
        "/preferences",
        json={
            "genre": "Mystery",
            "author": "Agatha Christie",
            "min_year": 1920,
            "max_year": 1970,
        },
        headers={"Authorization": "Bearer testuser"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Preferences saved successfully"}

    # Verify that preferences were updated
    response = await client.get("/recommendations", headers={"Authorization": "Bearer testuser"})
    assert response.status_code == 200
    data = response.json()
    assert data["books"] == []  # No matches for updated preferences


@pytest.mark.asyncio
async def test_save_preferences_create_new(client: AsyncClient, test_db):
    # Create a new user
    new_user = models.User(username="newuser")
    test_db.add(new_user)
    await test_db.commit()

    response = await client.post(
        "/preferences",
        json={
            "genre": "Romance",
            "author": "Jane Austen",
            "min_year": 1800,
            "max_year": 1900,
        },
        headers={"Authorization": "Bearer newuser"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Preferences saved successfully"}


@pytest.mark.asyncio
async def test_get_recommendations_with_partial_preferences(client: AsyncClient, create_user, create_books):
    # Update user preferences to only include genre
    response = await client.post(
        "/preferences",
        json={
            "genre": "Fantasy",
            "author": None,
            "min_year": None,
            "max_year": None,
        },
        headers={"Authorization": "Bearer testuser"},
    )
    assert response.status_code == 200

    # Fetch recommendations
    response = await client.get("/recommendations", headers={"Authorization": "Bearer testuser"})
    assert response.status_code == 200
    data = response.json()
    assert "recommendation_summary" in data
    assert len(data["books"]) > 0
    assert any(book["title"] == "The Hobbit" for book in data["books"])


@pytest.mark.asyncio
async def test_get_recommendations_with_no_books(client: AsyncClient, create_user, test_db):
    # Clear all books from the database
    await test_db.execute("DELETE FROM books")
    await test_db.commit()

    response = await client.get("/recommendations", headers={"Authorization": "Bearer testuser"})
    assert response.status_code == 200
    assert response.json() == {"message": "Sorry, we couldn't find any books matching your preferences."}


@pytest.mark.asyncio
async def test_get_recommendations_llm_integration(client: AsyncClient, create_user, create_books, mocker):
    # Mock the LLM response
    mock_llm = mocker.patch("app.api.routes.recommendations.ChatOllama.invoke")
    mock_llm.return_value = "Here are some great books for you to explore!"

    response = await client.get("/recommendations", headers={"Authorization": "Bearer testuser"})
    assert response.status_code == 200
    data = response.json()
    assert "recommendation_summary" in data
    assert data["recommendation_summary"] == "Here are some great books for you to explore!"
    assert len(data["books"]) > 0


# Additional test for contextual LLM recommendation summary
@pytest.mark.asyncio
async def test_get_recommendations_llm_context_summary(client: AsyncClient, create_user, create_books, mocker):
    # Update user preferences to trigger LLM
    await client.post(
        "/preferences",
        json={
            "genre": "Fantasy",
            "author": "Tolkien",
            "min_year": 1930,
            "max_year": 1960,
        },
        headers={"Authorization": "Bearer testuser"},
    )

    # Mock the LLM response to return a specific summary
    mock_llm = mocker.patch("app.api.routes.recommendations.ChatOllama.invoke")
    mock_llm.return_value = type("MockLLMResponse", (), {"content": "Explore timeless fantasy classics that shaped modern storytelling."})()

    response = await client.get("/recommendations", headers={"Authorization": "Bearer testuser"})
    assert response.status_code == 200
    data = response.json()
    assert "recommendation_summary" in data
    assert data["recommendation_summary"].startswith("Explore timeless fantasy")
    assert len(data["books"]) > 0
