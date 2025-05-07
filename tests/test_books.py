import pytest
from httpx import AsyncClient
from fastapi import status
from app.main import app
from app.db import models
from app.db.database import SessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

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
        async def _create_book(title: str, author: str, genre: str, year_published: int, summary: str):
            book = models.Book(
                title=title,
                author=author,
                genre=genre,
                year_published=year_published,
                summary=summary
            )
            test_db.add(book)
            await test_db.commit()
            await test_db.refresh(book)
            return book
        return _create_book

    @pytest.mark.asyncio
    async def test_add_book(test_client, mocker):
        mock_generate_and_update_summary = mocker.patch(
            "app.api.routes.books.generate_and_update_summary", new_callable=AsyncMock
        )
        file_content = b"Dummy PDF content"
        files = {"file": ("test.pdf", file_content, "application/pdf")}
        form_data = {
            "title": "Test Book",
            "author": "Test Author",
            "genre": "Fiction",
            "year_published": 2023,
            "quick": False
        }
        response = await test_client.post(
            "/", data=form_data, files=files, headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Test Book"
        assert data["summary"] == "Generating..."
        mock_generate_and_update_summary.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_books(test_client, create_test_book):
        await create_test_book("Book 1", "Author 1", "Genre 1", 2020, "Summary 1")
        await create_test_book("Book 2", "Author 2", "Genre 2", 2021, "Summary 2")
        response = await test_client.get("/", headers={"Authorization": "Bearer test_token"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == "Book 1"
        assert data[1]["title"] == "Book 2"

    @pytest.mark.asyncio
    async def test_get_book(test_client, create_test_book):
        book = await create_test_book("Specific Book", "Author", "Genre", 2022, "Specific Summary")
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
    async def test_get_summary_status_ready(test_client, create_test_book):
        book = await create_test_book("Summary Ready Book", "Author", "Genre", 2022, "This is a summary.")
        response = await test_client.get(f"/{book.id}/summary/status", headers={"Authorization": "Bearer test_token"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["summary_ready"] is True

    @pytest.mark.asyncio
    async def test_get_summary_status_generating(test_client, create_test_book):
        book = await create_test_book("Summary Generating Book", "Author", "Genre", 2022, "Generating...")
        response = await test_client.get(f"/{book.id}/summary/status", headers={"Authorization": "Bearer test_token"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["summary_ready"] is False

    @pytest.mark.asyncio
    async def test_get_summary(test_client, create_test_book, mocker):
        book = await create_test_book("Summary Book", "Author", "Genre", 2022, "This is a book summary.")
        mock_generate_summary = mocker.patch(
            "app.api.routes.books.generate_summary", new_callable=AsyncMock, return_value="Generated AI Summary"
        )
        response = await test_client.get(f"/{book.id}/summary", headers={"Authorization": "Bearer test_token"})
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["generated_summary"] == "Generated AI Summary"
        mock_generate_summary.assert_called_once_with(
            f"Summarize the following book content:\n\nTitle: {book.title}\n\nSummary: {book.summary}"
        )
