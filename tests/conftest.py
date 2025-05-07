import sys
from pathlib import Path

# Add the project root directory to PYTHONPATH
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from asgi_lifespan import LifespanManager
from app.main import app
from app.db.database import get_db, SessionLocal

@pytest_asyncio.fixture
async def client(db_session):
    print("🧪 Starting client fixture")

    async def override_get_db():
        print("🧪 Overriding get_db")
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    print("🧪 Starting LifespanManager")
    async with LifespanManager(app):
        print("✅ LifespanManager started")
        async with AsyncClient(app=app, base_url="http://testserver") as ac:
            print("✅ AsyncClient ready")
            yield ac

@pytest_asyncio.fixture
async def db_session():
    async with SessionLocal() as session:
        yield session
