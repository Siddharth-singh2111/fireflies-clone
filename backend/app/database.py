"""Database engine, session factory, and the declarative Base.

We use SQLAlchemy 2.0's typed ORM. `check_same_thread=False` is required for
SQLite when used with FastAPI's threaded request handling; every request still
gets its own Session via the `get_db` dependency, so there is no shared mutable
state across requests.
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base all ORM models inherit from."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a request-scoped session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
