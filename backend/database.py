"""
database.py — SQLAlchemy SQLite setup for PredictOps backend.

Creates the engine, session factory, and a declarative base that all
ORM models inherit from.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# SQLite file is created next to this file automatically
DATABASE_URL = "sqlite:///./predictops.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # needed for SQLite + FastAPI threads
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def get_db():
    """
    FastAPI dependency that yields a database session and ensures it is
    properly closed after the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
