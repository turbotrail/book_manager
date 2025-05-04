# book_manager/app/api/routes/reviews.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.database import SessionLocal
from app.db import models
from app.schemas.review import ReviewIn, ReviewOut
from app.core.security import get_current_user

router = APIRouter()

async def get_db():
    async with SessionLocal() as session:
        yield session

@router.post("/{book_id}/reviews", response_model=ReviewOut)
async def add_review(book_id: int, review: ReviewIn, db: AsyncSession = Depends(get_db),current_user: str = Depends(get_current_user)):
    result = await db.execute(select(models.Book).where(models.Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    print(f"Adding review for book {book_id} by user {current_user}")
    new_review = models.Review(**review.dict(), book_id=book_id, user_id=current_user)
    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)
    return new_review

@router.get("/{book_id}/reviews", response_model=list[ReviewOut])
async def get_reviews(book_id: int, db: AsyncSession = Depends(get_db),current_user: str = Depends(get_current_user)):
    result = await db.execute(select(models.Review).where(models.Review.book_id == book_id))
    return result.scalars().all()