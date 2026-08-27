"""
tests/conftest.py
--------------------
Shared pytest fixtures. Every test runs against a fresh, isolated SQLite
database (never your real Postgres) so tests are fast, repeatable, and
can never corrupt real user data.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


@pytest.fixture
def test_db(tmp_path):
    """Fresh SQLite DB per test, auto-cleaned up afterward."""
    db_path = tmp_path / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    import database.db as dbmod
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    dbmod.engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    dbmod.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=dbmod.engine)

    yield dbmod.SessionLocal


@pytest.fixture
def client(test_db):
    """FastAPI TestClient wired to the isolated test database."""
    from mainn import app
    from fastapi.testclient import TestClient
    from database.db import Base
    import database.db as dbmod

    # main.py's Base.metadata.create_all() only runs once (Python caches
    # imports across tests in the same session) - so each fresh temp
    # database needs its tables created explicitly here, or every test
    # after the first one fails with "no such table".
    Base.metadata.create_all(bind=dbmod.engine)

    return TestClient(app)