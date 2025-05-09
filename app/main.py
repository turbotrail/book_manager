# book_manager/app/main.py
from fastapi import FastAPI
from app.api.routes import books, reviews , auth , recommendations
from app.core.config import settings
from app.db.database import init_db
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer

app = FastAPI(title="Intelligent Book Management System")

@app.on_event("startup")
async def startup():
    await init_db()

# Allow CORS for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(books.router, prefix="/books", tags=["Books"])
app.include_router(reviews.router, prefix="/books", tags=["Reviews"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])

@app.get("/")
def root():
    return {"message": "Welcome to the Intelligent Book Management System"}