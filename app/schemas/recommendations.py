# --- Recommendation Schemas ---
from pydantic import BaseModel
from typing import Optional, List

class UserPreferences(BaseModel):
    genre: Optional[str] = None
    author: Optional[str] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None

class BookRecommendation(BaseModel):
    title: str
    author: str
    year_published: Optional[int]
    summary: Optional[str]
    rating: Optional[float]
    confidence: Optional[str]

class RecommendationsResponse(BaseModel):
    message: str
    books: List[BookRecommendation]
