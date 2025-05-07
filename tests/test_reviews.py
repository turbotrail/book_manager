import pytest
from httpx import AsyncClient
from app.main import app
from app.db import models
from app.db.database import SessionLocal
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.fixture
async def test_db():
    async with SessionLocal() as session:
        yield session

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac: # pylint: disable=unexpected-keyword-arg
        yield ac

@pytest.fixture
async def mock_user():
    return "test_user"

@pytest.fixture
async def mock_book(test_db: AsyncSession):
    book = models.Book(id=1, title="Test Book", author="Test Author")
    test_db.add(book)
    await test_db.commit()
    await test_db.refresh(book)
    return book

@pytest.fixture
async def mock_review(test_db: AsyncSession, mock_book: models.Book, mock_user: str):
    review = models.Review(id=1, content="Great book!", book_id=mock_book.id, user_id=mock_user)
    test_db.add(review)
    await test_db.commit()
    await test_db.refresh(review)
    return review

@pytest.mark.asyncio
async def test_add_review(client: AsyncClient, mock_book: models.Book, mock_user: str):
    async with client as ac:
        review_data = {"content": "Amazing read!"}
        response = await ac.post(f"/{mock_book.id}/reviews", json=review_data, headers={"Authorization": f"Bearer {mock_user}"})
        assert response.status_code == 200
        assert response.json()["content"] == review_data["content"]
        assert response.json()["book_id"] == mock_book.id
        assert response.json()["user_id"] == mock_user

@pytest.mark.asyncio
async def test_add_review_book_not_found(client: AsyncClient, mock_user: str):
    async with client as ac:
        review_data = {"content": "Amazing read!"}
        response = await ac.post("/999/reviews", json=review_data, headers={"Authorization": f"Bearer {mock_user}"})
        assert response.status_code == 404
        assert response.json()["detail"] == "Book not found"

@pytest.mark.asyncio
async def test_get_reviews(client: AsyncClient, mock_book: models.Book, mock_review: models.Review, mock_user: str):
    async with client as ac:
        response = await ac.get(f"/{mock_book.id}/reviews", headers={"Authorization": f"Bearer {mock_user}"})
        assert response.status_code == 200
        reviews = response.json()
        assert len(reviews) == 1
        assert reviews[0]["content"] == mock_review.content
        assert reviews[0]["book_id"] == mock_book.id
        assert reviews[0]["user_id"] == mock_user