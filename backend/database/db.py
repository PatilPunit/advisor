"""
database/db.py
----------------
Connects FastAPI to PostgreSQL via SQLAlchemy.

Creates:
  - engine        : the actual DB connection
  - SessionLocal   : a factory for DB sessions (one per request)
  - Base          : the declarative base all models.py classes inherit from
  - get_db()      : FastAPI dependency that yields a session and closes it after
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# --------------------------------------------------------------------------
# DATABASE_URL
# --------------------------------------------------------------------------
# Format: postgresql://<user>:<password>@<host>:<port>/<database_name>
#
# Update the username/password below to match your local PostgreSQL setup.
# On most fresh installs, the default superuser is "postgres" with whatever
# password you set during install (or peer auth with no password on Linux -
# in that case you may need to create a dedicated DB user first).
#
# You can also set this via an environment variable instead of hardcoding it:
#   export DATABASE_URL="postgresql://postgres:yourpassword@localhost:5432/career_advisor"
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/career_advisor",
)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session, always closes it afterward."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()