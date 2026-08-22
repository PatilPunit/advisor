"""
skills_vocab.py
------------------
A single shared skill vocabulary + matching function used by the resume
extractor, the job-matching engine, and anywhere else that needs to detect
"which known skills appear in this text".

Beyond the original spec: instead of only recognizing skills already listed
in career_paths.csv, this merges in common industry keywords (Docker, AWS,
Git, etc.) that show up in job descriptions and resumes but aren't tied to
any single career in your dataset. Without this, job-matching against a
real job description would miss most of its actual requirements.
"""

from __future__ import annotations

import csv
import os
import re
from typing import List, Set

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAREER_PATHS_CSV = os.path.join(BASE_DIR, "dataset", "career_paths.csv")

# Common tech/tooling keywords that appear constantly in job descriptions
# and resumes but may not be an exact "required_skill" for any one career
# in career_paths.csv yet.
EXTRA_SKILLS = [
    "Docker", "Kubernetes", "AWS", "GCP", "Azure", "Git", "GitHub",
    "MongoDB", "PostgreSQL", "MySQL", "Redis", "GraphQL", "REST API",
    "TypeScript", "Flask", "Django", "FastAPI", "Scikit-learn",
    "OpenCV", "NLP", "CI/CD", "Bash", "Kafka", "Spark", "Airflow",
    "Tableau", "Excel", "PyTorch", "Keras",
]


def _normalize(text: str) -> str:
    return text.strip().lower()


def load_master_vocabulary(csv_path: str = CAREER_PATHS_CSV) -> List[str]:
    """
    Every unique skill across career_paths.csv, merged with EXTRA_SKILLS,
    deduplicated (case-insensitive), original casing preserved.
    """
    seen: Set[str] = set()
    vocabulary: List[str] = []

    if os.path.exists(csv_path):
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                for skill in [s.strip() for s in row["required_skills"].split(",") if s.strip()]:
                    key = _normalize(skill)
                    if key not in seen:
                        seen.add(key)
                        vocabulary.append(skill)

    for skill in EXTRA_SKILLS:
        key = _normalize(skill)
        if key not in seen:
            seen.add(key)
            vocabulary.append(skill)

    return vocabulary


def _skill_present(skill: str, text_lower: str) -> bool:
    """
    Word-boundary match for short/single-token skills (avoids "R" matching
    inside "Regression"); substring match for multi-word or slash-containing
    skills (e.g. "AWS/GCP", "Machine Learning").
    """
    skill_lower = skill.lower()
    is_single_token = " " not in skill_lower and "/" not in skill_lower

    if is_single_token and len(skill_lower) <= 4:
        pattern = r"\b" + re.escape(skill_lower) + r"\b"
        return re.search(pattern, text_lower) is not None

    return skill_lower in text_lower


def find_skills_in_text(text: str, vocabulary: List[str]) -> List[str]:
    """Returns every skill from `vocabulary` that appears in `text`, original casing."""
    text_lower = text.lower()
    return [skill for skill in vocabulary if _skill_present(skill, text_lower)]