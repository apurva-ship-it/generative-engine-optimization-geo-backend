"""Database setup using SQLAlchemy async engine."""
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Boolean, DateTime, func, Integer
from .config import Settings

settings = Settings()

DATABASE_URL = settings.database_url

engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=False, future=True)
# Correct async session maker
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass

# Dependency
from fastapi import Depends

def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
