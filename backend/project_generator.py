"""
project_generator.py
------------------------
Deliverable 6: AI Project Generator.

Given a domain + difficulty level, picks a fitting project from
project_bank.csv and enriches it with suggested skills and an estimated
timeline. Dataset suggestions and skill hints are curated per domain since
project_bank.csv doesn't track that level of detail yet.
"""

from __future__ import annotations

import csv
import os
import random
from typing import Dict, List, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_BANK_CSV = os.path.join(BASE_DIR, "dataset", "project_bank.csv")

TIMELINE_BY_DIFFICULTY = {
    "beginner": "1-2 Weeks",
    "intermediate": "2-4 Weeks",
    "advanced": "6-8 Weeks",
}

# Curated skill hints + example datasets per domain, since project_bank.csv
# doesn't carry this metadata yet. Extend this as your dataset grows.
DOMAIN_SKILLS = {
    "data science": ["Pandas", "NumPy", "Data Visualization", "Statistics"],
    "machine learning": ["Pandas", "Scikit-learn", "Model Evaluation"],
    "data analytics": ["Excel", "SQL", "Power BI", "Data Visualization"],
    "web development": ["HTML", "CSS", "JavaScript", "React"],
    "full stack + ai": ["React", "FastAPI", "Machine Learning", "Deployment"],
    "android development": ["Kotlin", "XML Layouts", "SQLite"],
    "cloud computing": ["Docker", "AWS/GCP", "Linux", "Networking"],
    "cyber security": ["Networking", "Linux", "Security Fundamentals"],
    "ai": ["Python", "Deep Learning", "Model Deployment"],
}

DOMAIN_DATASETS = {
    "data science": "Kaggle: Spotify Tracks Dataset",
    "machine learning": "Kaggle: Telecom Customer Churn Dataset",
    "data analytics": "Kaggle: Superstore Sales Dataset",
    "web development": "N/A - build from your own content",
    "full stack + ai": "Custom / user-generated data",
    "android development": "N/A - build from your own content",
    "cloud computing": "N/A - infra project, no dataset needed",
    "cyber security": "OWASP Juice Shop (practice target)",
    "ai": "Kaggle: relevant domain dataset",
}


def _load_project_bank(csv_path: str = PROJECT_BANK_CSV) -> List[dict]:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"project_bank.csv not found at: {csv_path}")
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def generate_project(domain: str, level: str) -> Optional[Dict]:
    """
    Returns a personalized project recommendation matching the given
    domain + difficulty level, or None if nothing matches.
    """
    projects = _load_project_bank()
    domain_lower = domain.strip().lower()
    level_lower = level.strip().lower()

    matches = [
        p for p in projects
        if p["domain"].strip().lower() == domain_lower
        and p["difficulty"].strip().lower() == level_lower
    ]

    if not matches:
        return None

    chosen = random.choice(matches)

    return {
        "project_name": chosen["project_name"],
        "domain": chosen["domain"],
        "difficulty": chosen["difficulty"],
        "dataset": DOMAIN_DATASETS.get(domain_lower, "N/A"),
        "skills": DOMAIN_SKILLS.get(domain_lower, []),
        "timeline": TIMELINE_BY_DIFFICULTY.get(level_lower, "2-4 Weeks"),
    }


def list_available_domains() -> List[str]:
    projects = _load_project_bank()
    return sorted({p["domain"] for p in projects})