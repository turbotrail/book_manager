import pytest
from httpx import AsyncClient
from fastapi import status
from app.main import app
from app.db import models
from app.db.database import SessionLocal
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.fixture
async def test_db():
    async with SessionLocal() as session:
        yield session

@pytest.fixture
async def test_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def create_test_book(test_db: AsyncSession):
    async def _create_book(title: str, summary: str):
        book = models.Book(title=title, summary=summary)
        test_db.add(book)
        await test_db.commit()
        await test_db.refresh(book)
        return book
    return _create_book

@pytest.mark.asyncio
async def test_add_book(test_client, test_db):
    response = await test_client.post(
        "/",
        json={"title": "Test Book", "summary": "This is a test book."},
        headers={"Authorization": "Bearer test_token"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Test Book"
    assert data["summary"] == "This is a test book."

@pytest.mark.asyncio
async def test_get_all_books(test_client, create_test_book):
    await create_test_book("Book 1", "Summary 1")
    await create_test_book("Book 2", "Summary 2")
    response = await test_client.get("/", headers={"Authorization": "Bearer test_token"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Book 1"
    assert data[1]["title"] == "Book 2"

@pytest.mark.asyncio
async def test_get_book(test_client, create_test_book):
    book = await create_test_book("Specific Book", "Specific Summary")
    response = await test_client.get(f"/{book.id}", headers={"Authorization": "Bearer test_token"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Specific Book"
    assert data["summary"] == "Specific Summary"

@pytest.mark.asyncio
async def test_get_book_not_found(test_client):
    response = await test_client.get("/999", headers={"Authorization": "Bearer test_token"})
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Book not found"

@pytest.mark.asyncio
async def test_get_summary(test_client, create_test_book, mocker):
    book = await create_test_book("Summary Book", "This is a book summary.")
    mock_generate_summary = mocker.patch("app.services.ai_summary.generate_summary", return_value="Generated AI Summary")
    response = await test_client.get(f"/{book.id}/summary", headers={"Authorization": "Bearer test_token"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["generated_summary"] == "Generated AI Summary"
    mock_generate_summary.assert_called_once_with(
        f"Summarize the following book content:\n\nTitle: {book.title}\n\nSummary: {book.summary}"
    )