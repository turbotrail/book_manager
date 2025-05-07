from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.database import get_db, SessionLocal
from app.db import models
from app.schemas import recommendations
from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from anyio import to_thread
from app.api.dependencies import get_current_user
from app.core.prompt_templates import RECOMMENDATION_PROMPT

router = APIRouter()

@router.post("/preferences")
async def save_preferences(preferences: recommendations.UserPreferences, db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    # Overwrite or create user preference
    result = await db.execute(select(models.User).where(models.User.username == current_user))
    existing = result.scalar_one_or_none()

    if existing:
        existing.genre = preferences.genre
        existing.author = preferences.author
        existing.min_year = preferences.min_year
        existing.max_year = preferences.max_year
    else:
        new_pref = models.User(user_id=current_user, **preferences.dict())
        db.add(new_pref)

    await db.commit()
    return {"message": "Preferences saved successfully"}

@router.get("/recommendations")
async def get_recommendations(db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    result = await db.execute(select(models.User).where(models.User.username == current_user))
    pref = result.scalar_one_or_none()

    if not pref:
        raise HTTPException(status_code=404, detail="No preferences found for user")

    book_query = await db.execute(select(models.Book))
    all_books = book_query.scalars().all()

    matched_books = []

    for book in all_books:
        match_score = 0.0

        if pref.genre and pref.genre.lower() in book.genre.lower():
            match_score += 0.4
        if pref.author and pref.author.lower() in book.author.lower():
            match_score += 0.3
        if pref.min_year and book.year_published >= pref.min_year:
            match_score += 0.15
        if pref.max_year and book.year_published <= pref.max_year:
            match_score += 0.15

        if match_score > 0:
            rating = round(match_score * 5, 1)
            confidence = "High" if match_score >= 0.8 else "Medium" if match_score >= 0.5 else "Low"

            matched_books.append({
                "title": book.title,
                "author": book.author,
                "year_published": book.year_published,
                "summary": book.summary,
                "rating": rating,
                "confidence": confidence
            })

    if matched_books:
        matched_books.sort(key=lambda x: x["rating"], reverse=True)
        # Prepare input for LLM to get a contextual recommendation message
        book_titles = ", ".join([book["title"] for book in matched_books])
        prompt_template = RECOMMENDATION_PROMPT
        llm = ChatOllama(model="llama3", temperature=0.7, base_url="http://host.docker.internal:11434")
        llm_prompt = prompt_template.format(
            genre=pref.genre or "Any",
            author=pref.author or "Any",
            min_year=pref.min_year or "Any",
            max_year=pref.max_year or "Any",
            book_titles=book_titles
        )
        recommendation_summary = await to_thread.run_sync(llm.invoke, llm_prompt)
        recommendation_text = (
            recommendation_summary.content
            if hasattr(recommendation_summary, "content")
            else str(recommendation_summary)
        ).strip().split("\n")[0]
        return {
            "recommendation_summary": recommendation_text,
            "books": matched_books
        }
    else:
        return {"message": "Sorry, we couldn't find any books matching your preferences."}