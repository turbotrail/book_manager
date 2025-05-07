from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.database import SessionLocal
from app.db import models
from app.schemas.book import BookOut
from app.core.security import get_current_user
import os
from app.services.ai_summary import generate_summary

# LangChain imports
from langchain.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain_ollama import ChatOllama
from app.core.prompt_templates import SUMMARY_PROMPT_TEMPLATE
import tempfile
from anyio import to_thread

router = APIRouter()

async def get_db():
    async with SessionLocal() as session:
        yield session

def choose_summary_chain(llm, docs):
    # Choose refine if many long documents, else use map_reduce
    avg_length = sum(len(doc.page_content) for doc in docs) / len(docs)
    if len(docs) > 20 or avg_length > 1000:
        return load_summarize_chain(llm, chain_type="refine")
    else:
        return load_summarize_chain(llm, chain_type="map_reduce")

async def generate_and_update_summary(book_id: int, file_path: str, quick: bool):
    loader = PyMuPDFLoader(file_path)
    pages = loader.load()

    if quick:
        pages = pages[:10]

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    docs = splitter.split_documents(pages)

    llm = ChatOllama(model="llama3", base_url="http://host.docker.internal:11434")

    prompt_template = SUMMARY_PROMPT_TEMPLATE

    chain = choose_summary_chain(llm, docs)
    chain.llm_chain.prompt = prompt_template

    def summarize_blocking():
        res = chain.invoke(docs)
        return res["output_text"] if isinstance(res, dict) else res

    summary = await to_thread.run_sync(summarize_blocking)

    async with SessionLocal() as db:
        result = await db.execute(select(models.Book).where(models.Book.id == book_id))
        book = result.scalar_one_or_none()
        if book:
            book.summary = summary
            db.add(book)
            await db.commit()
            await db.refresh(book)

    os.remove(file_path)

@router.post("/", response_model=BookOut)
async def add_book(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    author: str = Form(...),
    genre: str = Form(...),
    year_published: int = Form(...),
    file: UploadFile = File(...),
    quick: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    db_book = models.Book(
        title=title,
        author=author,
        genre=genre,
        year_published=year_published,
        summary="Generating..."
    )
    db.add(db_book)
    await db.commit()
    await db.refresh(db_book)

    background_tasks.add_task(generate_and_update_summary, db_book.id, tmp_path, quick)

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

@router.get("/{book_id}/summary/status")
async def get_summary_status(book_id: int, db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    result = await db.execute(select(models.Book).where(models.Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    is_ready = book.summary and book.summary.strip().lower() != "generating..."
    return {"book_id": book.id, "summary_ready": is_ready}

@router.get("/{book_id}/summary")
async def get_summary(book_id: int, db: AsyncSession = Depends(get_db),current_user: str = Depends(get_current_user)):
    result = await db.execute(select(models.Book).where(models.Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    prompt = f"Summarize the following book content:\n\nTitle: {book.title}\n\nSummary: {book.summary}"
    ai_summary = await generate_summary(prompt)
    return {"generated_summary": ai_summary}