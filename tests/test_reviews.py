import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from app.db import models
from app.db.database import override_get_db, get_db
from fastapi import status

@pytest_asyncio.fixture
async def test_db():
    async with override_get_db() as session:
        yield session

@pytest_asyncio.fixture
async def client():
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def create_test_user(test_db: AsyncSession):
    async def _create_user(user_id: str = "testuser"):
        user = models.User(id=user_id, username=user_id)
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        return user
    return _create_user

@pytest_asyncio.fixture
async def create_test_book(test_db: AsyncSession):
    async def _create_book(book_id: int = 1):
        book = models.Book(id=book_id, title="Sample", author="Author", genre="Fiction", year_published=2020, summary="Test Summary")
        test_db.add(book)
        await test_db.commit()
        await test_db.refresh(book)
        return book
    return _create_book

@pytest.mark.asyncio
async def test_add_review_success(client: AsyncClient, test_db: AsyncSession, create_test_user, create_test_book):
    user = await create_test_user()
    book = await create_test_book()
    review_data = {"rating": 4, "comment": "Nice read."}

    response = await client.post(f"/{book.id}/reviews", json=review_data, headers={"Authorization": f"Bearer {user.username}"})
    assert response.status_code == 200
    data = response.json()
    assert data["rating"] == 4
    assert data["comment"] == "Nice read."
    assert data["book_id"] == book.id
    assert data["user_id"] == user.id

@pytest.mark.asyncio
async def test_add_review_book_not_found(client: AsyncClient, create_test_user):
    user = await create_test_user()
    review_data = {"rating": 5, "comment": "Excellent!"}

    response = await client.post("/999/reviews", json=review_data, headers={"Authorization": f"Bearer {user.username}"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"

@pytest.mark.asyncio
async def test_get_reviews_success(client: AsyncClient, test_db: AsyncSession, create_test_user, create_test_book):
    user = await create_test_user()
    book = await create_test_book()
    review = models.Review(rating=5, comment="Loved it!", book_id=book.id, user_id=user.id)
    test_db.add(review)
    await test_db.commit()

    response = await client.get(f"/{book.id}/reviews", headers={"Authorization": f"Bearer {user.username}"})
    assert response.status_code == 200
    reviews = response.json()
    assert len(reviews) == 1
    assert reviews[0]["comment"] == "Loved it!"

@pytest.mark.asyncio
async def test_get_reviews_no_reviews(client: AsyncClient, create_test_user, create_test_book):
    user = await create_test_user()
    book = await create_test_book()

    response = await client.get(f"/{book.id}/reviews", headers={"Authorization": f"Bearer {user.username}"})
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_add_review_unauthenticated(client: AsyncClient, create_test_book):
    book = await create_test_book()
    response = await client.post(f"/{book.id}/reviews", json={"rating": 3, "comment": "Ok"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_reviews_unauthenticated(client: AsyncClient, create_test_book):
    book = await create_test_book()
    response = await client.get(f"/{book.id}/reviews")
    assert response.status_code == 401
