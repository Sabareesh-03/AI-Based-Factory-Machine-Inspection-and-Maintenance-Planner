"""
Database Initialization
Creates all tables defined by SQLAlchemy models.
Safe to run multiple times — will not delete existing data.
"""

import sys
import os

# Allow running from backend/ directory directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import engine, Base
import app.models  # noqa: F401 — side-effect import: registers all models with Base.metadata


def init_db():
    """
    Create all database tables.
    Uses CREATE TABLE IF NOT EXISTS — safe to run multiple times.
    """
    print("🔧 Initializing database...")
    print(f"   Engine: {engine.url}")

    Base.metadata.create_all(bind=engine)

    # Print created tables
    tables = list(Base.metadata.tables.keys())
    print(f"✅ Tables ready ({len(tables)}):")
    for table in sorted(tables):
        print(f"   • {table}")
    print("✅ Database initialization complete.")


if __name__ == "__main__":
    init_db()
