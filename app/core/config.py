# book_manager/app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Book Management System"
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/booksdb"
    LLAMA_ENDPOINT: str = "http://host.docker.internal:11434" # adjust based on Ollama setup
    SECRET_KEY: str = "your_secret_key"
    ALGORITHM: str = "HS256"

settings = Settings()