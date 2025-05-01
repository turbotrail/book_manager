# book_manager/app/schemas/book.py
from pydantic import BaseModel

class BookIn(BaseModel):
    title: str
    author: str
    genre: str
    year_published: int
    summary: str

class BookOut(BookIn):
    id: int