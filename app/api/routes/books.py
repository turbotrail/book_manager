# book_manager/app/api/routes/books.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.database import SessionLocal
from app.db import models
from app.schemas.book import BookIn, BookOut
from app.services.ai_summary import generate_summary
from app.core.security import get_current_user

router = APIRouter()

async def get_db():
    async with SessionLocal() as session:
        yield session

@router.post("/", response_model=BookOut)
async def add_book(book: BookIn, db: AsyncSession = Depends(get_db),current_user: str = Depends(get_current_user)):
    db_book = models.Book(**book.dict())
    db.add(db_book)
    await db.commit()
    await db.refresh(db_book)
    return db_book

@router.get("/", response_model=list[BookOut])
async def get_all_books(db: AsyncSession = Depends(get_db),current_user: str = Depends(get_current_user)):
    result = await db.execute(select(models.Book))
    return result.scalars().all()

@router.get("/{book_id}", response_model=BookOut)
async def get_book(book_id: int, db: AsyncSession = Depends(get_db),current_user: str = Depends(get_current_user)):
    result = await db.execute(select(models.Book).where(models.Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router.get("/{book_id}/summary")
async def get_summary(book_id: int, db: AsyncSession = Depends(get_db),current_user: str = Depends(get_current_user)):
    result = await db.execute(select(models.Book).where(models.Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    prompt = f"Summarize the following book content:\n\nTitle: {book.title}\n\nSummary: {book.summary}"
    ai_summary = await generate_summary(prompt)
    return {"generated_summary": ai_summary}