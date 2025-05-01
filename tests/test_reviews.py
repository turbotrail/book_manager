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
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def create_test_book(test_db: AsyncSession):
    async def _create_test_book(book_id: int):
        book = models.Book(id=book_id, title="Test Book", author="Test Author")
        test_db.add(book)
        await test_db.commit()
        await test_db.refresh(book)
        return book
    return _create_test_book

@pytest.mark.asyncio
async def test_add_review(client: AsyncClient, test_db: AsyncSession, create_test_book):
    # Arrange
    book = await create_test_book(book_id=1)
    review_data = {"rating": 5, "comment": "Great book!"}

    # Act
    response = await client.post(f"/1/reviews", json=review_data)

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["rating"] == review_data["rating"]
    assert response_data["comment"] == review_data["comment"]
    assert response_data["book_id"] == book.id

@pytest.mark.asyncio
async def test_add_review_book_not_found(client: AsyncClient):
    # Arrange
    review_data = {"rating": 5, "comment": "Great book!"}

    # Act
    response = await client.post(f"/999/reviews", json=review_data)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"

@pytest.mark.asyncio
async def test_get_reviews(client: AsyncClient, test_db: AsyncSession, create_test_book):
    # Arrange
    book = await create_test_book(book_id=1)
    review = models.Review(rating=5, comment="Great book!", book_id=book.id)
    test_db.add(review)
    await test_db.commit()
    await test_db.refresh(review)

    # Act
    response = await client.get(f"/1/reviews")

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 1
    assert response_data[0]["rating"] == review.rating
    assert response_data[0]["comment"] == review.comment
    assert response_data[0]["book_id"] == book.id

@pytest.mark.asyncio
async def test_get_reviews_no_reviews(client: AsyncClient, create_test_book):
    # Arrange
    await create_test_book(book_id=1)

    # Act
    response = await client.get(f"/1/reviews")

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert response_data == []