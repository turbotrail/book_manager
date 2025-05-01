# book_manager/app/schemas/review.py
from pydantic import BaseModel

class ReviewIn(BaseModel):
    user_id: str
    review_text: str
    rating: int

class ReviewOut(ReviewIn):
    id: int
    book_id: int