import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from app.main import app
from app.db.database import get_db
from app.core.security import get_current_user

client = TestClient(app)

def override_get_current_user():
    return "mockuser"

def override_get_db_with_book(book=None):
    async def _override():
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = book
        mock_result.scalars.return_value.all.return_value = [book] if book else []

        mock_session = MagicMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.add = MagicMock()

        yield mock_session

    return _override

app.dependency_overrides[get_current_user] = override_get_current_user

@patch("app.api.routes.books.SessionLocal")
@patch("app.api.routes.books.generate_and_update_summary", new_callable=AsyncMock)
def test_add_book(mock_summary_task, mock_session_local):
    book_data = {
        "title": "Test Book",
        "author": "Author Name",
        "genre": "Fiction",
        "year_published": 2021,
        "quick": "true"
    }
    app.dependency_overrides[get_db] = override_get_db_with_book()
    os.makedirs("tests", exist_ok=True)
    with open("tests/sample.pdf", "wb") as f:
        f.write(b"%PDF-1.4 test content")

    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__.return_value = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session_local.return_value = mock_session

    with open("tests/sample.pdf", "rb") as f:
        response = client.post("/books/", data=book_data, files={"file": f})
    assert response.status_code == 200
    assert "id" in response.json()
    os.remove("tests/sample.pdf")

@patch("app.api.routes.books.SessionLocal")
def test_get_all_books(mock_session_local):
    mock_book = MagicMock()
    mock_book.id = 1
    mock_book.title = "Test"
    mock_book.author = "Author Name"
    mock_book.genre = "Fiction"
    mock_book.year_published = 2021
    mock_book.summary = None
    app.dependency_overrides[get_db] = override_get_db_with_book()

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [mock_book]
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__.return_value = AsyncMock()
    mock_session_local.return_value = mock_session

    response = client.get("/books/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@patch("app.api.routes.books.SessionLocal")
def test_get_book(mock_session_local):
    mock_book = MagicMock()
    mock_book.id = 1
    mock_book.title = "Test"
    app.dependency_overrides[get_db] = override_get_db_with_book()

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_book
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__.return_value = AsyncMock()
    mock_session_local.return_value = mock_session

    response = client.get("/books/1")
    assert response.status_code == 200
    assert response.json()["title"] == "Test"

@patch("app.api.routes.books.SessionLocal")
def test_get_summary_status(mock_session_local):
    mock_book = MagicMock()
    mock_book.id = 1
    mock_book.summary = "This is a summary."
    app.dependency_overrides[get_db] = override_get_db_with_book()

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_book
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__.return_value = AsyncMock()
    mock_session_local.return_value = mock_session

    response = client.get("/books/1/summary/status")
    assert response.status_code == 200
    assert response.json()["summary_ready"] is True

@patch("app.api.routes.books.SessionLocal")
@patch("app.api.routes.books.generate_summary", new_callable=AsyncMock)
def test_get_summary(mock_gen, mock_session_local):
    mock_book = MagicMock()
    mock_book.id = 1
    mock_book.title = "Mock Title"
    mock_book.summary = "mock summary"
    mock_gen.return_value = "Generated summary"
    app.dependency_overrides[get_db] = override_get_db_with_book()

    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_book
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__.return_value = AsyncMock()
    mock_session_local.return_value = mock_session

    response = client.get("/books/1/summary")
    assert response.status_code == 200
    assert "generated_summary" in response.json()