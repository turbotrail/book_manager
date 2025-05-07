# book_manager/app/schemas/review.py
from pydantic import BaseModel

class ReviewIn(BaseModel):
    review_text: str
    rating: int

class ReviewOut(ReviewIn):
    user_id: str
    book_id: int