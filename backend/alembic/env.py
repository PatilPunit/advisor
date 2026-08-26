"""
alembic/env.py
------------------
Customized to:
  1. Read DATABASE_URL from your .env file (via python-dotenv), instead
     of hardcoding a connection string in alembic.ini - one source of
     truth, matches how main.py connects.
  2. Import Base and every model from database/models.py, so
     `alembic revision --autogenerate` can actually detect schema changes
     by comparing your Python models against the live database.
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from dotenv import load_dotenv

# Make backend/ importable (this file lives in backend/alembic/)
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

# Explicitly point at backend/.env rather than relying on load_dotenv()'s
# working-directory guessing - alembic can be invoked from any directory,
# and load_dotenv() with no path only checks the current working directory
# and its parents, which silently fails if you run `alembic` from
# somewhere other than backend/.
load_dotenv(dotenv_path=os.path.join(BACKEND_DIR, ".env"))

from database.db import Base
from database import models  # noqa: F401 - import registers every model on Base.metadata

config = context.config
DATABASE_URL="postgresql://postgres:yourpassword@localhost:5432/career_advisor"
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError(
        f"DATABASE_URL not found. Checked for a .env file at: {os.path.join(BACKEND_DIR, '.env')}\n"
        f"Make sure that file exists and contains a line like:\n"
        f"  DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/career_advisor"
    )
config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    from sqlalchemy import create_engine

    url = config.get_main_option("sqlalchemy.url")
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()