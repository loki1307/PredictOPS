"""
database.py — SQLAlchemy SQLite setup for PredictOps backend.

Creates the engine, session factory, and a declarative base that all
ORM models inherit from.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# In production (Fly.io), use the persistent volume at /data/
# Locally, fall back to a file next to this script.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./predictops.db")

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
