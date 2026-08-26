"""
logging_config.py
---------------------
Deliverable 5: Logging System.

Two log files:
  logs/application.log - every important user action (login, resume
                          upload, roadmap generation, job match, etc.)
  logs/error.log       - warnings and errors only, for fast triage

Uses Python's built-in logging module (no extra dependency needed) with
rotating file handlers, so logs don't grow forever unbounded.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("career_advisor")
    logger.setLevel(logging.INFO)

    if logger.handlers:  # avoid duplicate handlers on uvicorn --reload
        return logger

    formatter = logging.Formatter(LOG_FORMAT)

    # application.log - everything INFO and above (normal activity)
    app_handler = RotatingFileHandler(
        os.path.join(LOGS_DIR, "application.log"), maxBytes=5_000_000, backupCount=3,
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(formatter)
    logger.addHandler(app_handler)

    # error.log - only WARNING and above, for fast triage without noise
    error_handler = RotatingFileHandler(
        os.path.join(LOGS_DIR, "error.log"), maxBytes=5_000_000, backupCount=3,
    )
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    # Also print to console during development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


logger = setup_logging()


# --------------------------------------------------------------------------
# Convenience functions for the specific actions the spec calls out
# --------------------------------------------------------------------------

def log_user_login(email: str, success: bool) -> None:
    if success:
        logger.info(f"LOGIN success | email={email}")
    else:
        logger.warning(f"LOGIN failed | email={email}")


def log_resume_upload(user_id, filename: str, score: int) -> None:
    logger.info(f"RESUME_UPLOAD | user_id={user_id} | file={filename} | score={score}")


def log_roadmap_generation(user_id, career: str) -> None:
    logger.info(f"ROADMAP_GENERATED | user_id={user_id} | career={career}")


def log_job_match(user_id, match_score: int) -> None:
    logger.info(f"JOB_MATCH | user_id={user_id} | score={match_score}")


def log_error(context: str, error: Exception) -> None:
    logger.error(f"ERROR in {context}: {type(error).__name__}: {error}")