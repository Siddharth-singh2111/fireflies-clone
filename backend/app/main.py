"""FastAPI application entry point.

Wires CORS, routers, health check, and a global exception handler. Tables are
created on startup for the SQLite demo (no migration step needed to run); in a
production Postgres setup you'd swap this for Alembic migrations.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import Base, engine
from app.routers import (
    action_items,
    chat,
    export,
    meetings,
    misc,
    search,
    segments,
)

logger = logging.getLogger("fireflies")
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Backend API for a Fireflies.ai-style meeting notes platform.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    # Enforce SQLite FK cascades (off by default in SQLite).
    if settings.database_url.startswith("sqlite"):
        from sqlalchemy import event

        @event.listens_for(engine, "connect")
        def _fk_pragma(dbapi_conn, _record):  # noqa: ANN001
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()

    Base.metadata.create_all(bind=engine)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
    """Never leak stack traces to the client; log server-side instead."""
    logger.exception("Unhandled error", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok", "llm_enabled": settings.llm_enabled}


app.include_router(misc.router)
app.include_router(meetings.router)
app.include_router(action_items.router)
app.include_router(segments.router)
app.include_router(search.router)
app.include_router(chat.router)
app.include_router(export.router)
