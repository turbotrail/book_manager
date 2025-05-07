import pytest
from httpx import AsyncClient
from fastapi import status
from app.main import app
from app.db import models
from app.db.database import SessionLocal

@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def test_db():
    async with SessionLocal() as session:
        yield session

@pytest.mark.asyncio
async def test_add_book(async_client, test_db):
    response = await async_client.post(
        "/",
        data={
            "title": "Test Book",
            "author": "Test Author",
            "genre": "Fiction",
            "year_published": 2023,
            "quick": False,
        },
        files={"file": ("test.pdf", b"Dummy PDF content", "application/pdf")},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Test Book"
    assert data["author"] == "Test Author"
    assert data["summary"] == "Generating..."

@pytest.mark.asyncio
async def test_get_all_books(async_client, test_db):
    # Add a book to the database for testing
    async with test_db as db:
        book = models.Book(
            title="Test Book",
            author="Test Author",
            genre="Fiction",
            year_published=2023,
            summary="Test Summary",
        )
        db.add(book)
        await db.commit()
        await db.refresh(book)

    response = await async_client.get("/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) > 0
    assert data[0]["title"] == "Test Book"

@pytest.mark.asyncio
async def test_get_book(async_client, test_db):
    # Add a book to the database for testing
    async with test_db as db:
        book = models.Book(
            title="Test Book",
            author="Test Author",
            genre="Fiction",
            year_published=2023,
            summary="Test Summary",
        )
        db.add(book)
        await db.commit()
        await db.refresh(book)

    response = await async_client.get(f"/{book.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Test Book"
    assert data["author"] == "Test Author"

@pytest.mark.asyncio
async def test_get_summary_status(async_client, test_db):
    # Add a book to the database for testing
    async with test_db as db:
        book = models.Book(
            title="Test Book",
            author="Test Author",
            genre="Fiction",
            year_published=2023,
            summary="Generating...",
        )
        db.add(book)
        await db.commit()
        await db.refresh(book)

    response = await async_client.get(f"/{book.id}/summary/status")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["book_id"] == book.id
    assert data["summary_ready"] is False

@pytest.mark.asyncio
async def test_get_summary(async_client, test_db):
    # Add a book to the database for testing
    async with test_db as db:
        book = models.Book(
            title="Test Book",
            author="Test Author",
            genre="Fiction",
            year_published=2023,
            summary="Test Summary",
        )
        db.add(book)
        await db.commit()
        await db.refresh(book)

    response = await async_client.get(f"/{book.id}/summary")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "generated_summary" in data