import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import get_db, engine, SessionLocal as TestingSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import models

@pytest.fixture(scope="module")
async def client():
    import time
    from sqlalchemy.exc import OperationalError
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            async with get_db() as db:
                await db.execute("SELECT 1")
            break
        except OperationalError:
            if attempt < max_attempts - 1:
                print(f"DB not ready yet ({attempt + 1}/{max_attempts}) — retrying...")
                time.sleep(3)
            else:
                raise

    app.dependency_overrides[get_db] = get_db
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def create_user():
    async with get_db() as session:
        async with session.begin():
            user = models.User(username="testuser", genre="Fantasy", author="Tolkien", min_year=1950, max_year=2000)
            session.add(user)
        await session.commit()
        return user

@pytest.fixture
async def create_books():
    books = [
        models.Book(title="The Hobbit", author="J.R.R. Tolkien", genre="Fantasy", year_published=1937, summary="A hobbit's adventure."),
        models.Book(title="The Fellowship of the Ring", author="J.R.R. Tolkien", genre="Fantasy", year_published=1954, summary="The first part of the epic journey."),
        models.Book(title="1984", author="George Orwell", genre="Dystopian", year_published=1949, summary="A dystopian novel."),
    ]
    async with get_db() as session:
        async with session.begin():
            session.add_all(books)
        await session.commit()
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
async def test_get_recommendations_no_matches(client: AsyncClient, create_user):
    async with get_db() as db:
        await db.execute("DELETE FROM books")
        await db.commit()

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
async def test_save_preferences_create_new(client: AsyncClient):
    async with get_db() as session:
        async with session.begin():
            new_user = models.User(username="newuser")
            session.add(new_user)
        await session.commit()

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
async def test_get_recommendations_with_no_books(client: AsyncClient, create_user):
    async with get_db() as db:
        await db.execute("DELETE FROM books")
        await db.commit()

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
