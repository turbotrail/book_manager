# book_manager/app/core/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Book Management System"
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/booksdb"
    LLAMA_ENDPOINT: str = "http://localhost:11434/api/generate"  # adjust based on Ollama setup

settings = Settings()