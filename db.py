"""
Database Configuration
SQLAlchemy setup with SQLite for development, PostgreSQL-ready for production.
Switch by setting DATABASE_URL in .env
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config.settings import settings

# ── Engine ────────────────────────────────────────────────────────────────────
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False  # Required for SQLite + FastAPI

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,          # SQL logging in dev mode
)

# Enable WAL mode for SQLite (better concurrency)
if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# ── Session Factory ───────────────────────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── Base Model ────────────────────────────────────────────────────────────────
Base = declarative_base()


# ── Dependency Injection ──────────────────────────────────────────────────────
def get_db():
    """FastAPI dependency — provides a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
