"""
resume/extractor.py
---------------------
Detects which known skills appear in a resume's text.

Instead of a hardcoded skill list per career, this pulls the master skill
vocabulary directly from dataset/career_paths.csv - every unique skill
across every career already in the system. This means the extractor
automatically supports every career you add later with zero code changes.
"""

from __future__ import annotations

import csv
import os
import re
from typing import List, Set

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
CAREER_PATHS_CSV = os.path.join(BASE_DIR, "dataset", "career_paths.csv")


def _load_skill_vocabulary(csv_path: str = CAREER_PATHS_CSV) -> List[str]:
    """
    Builds a deduplicated list of every skill mentioned across all careers
    in career_paths.csv, preserving original casing (e.g. "SQL", "Python").
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"career_paths.csv not found at: {csv_path}")

    seen: Set[str] = set()
    vocabulary: List[str] = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            skills = [s.strip() for s in row["required_skills"].split(",") if s.strip()]
            for skill in skills:
                key = skill.lower()
                if key not in seen:
                    seen.add(key)
                    vocabulary.append(skill)

    return vocabulary


def _skill_present(skill: str, text_lower: str) -> bool:
    """
    Checks whether `skill` appears in the resume text.

    Short or single-token skills (e.g. "R", "SQL") use word-boundary regex
    matching to avoid false positives (e.g. "R" incorrectly matching inside
    "Regression"). Multi-word or slash-containing skills (e.g. "AWS/GCP")
    fall back to a simple substring check, matching the original spec:
        if skill.lower() in resume_text.lower()
    """
    skill_lower = skill.lower()

    is_single_token = " " not in skill_lower and "/" not in skill_lower
    if is_single_token and len(skill_lower) <= 4:
        pattern = r"\b" + re.escape(skill_lower) + r"\b"
        return re.search(pattern, text_lower) is not None

    return skill_lower in text_lower


def extract_skills(resume_text: str, csv_path: str = CAREER_PATHS_CSV) -> List[str]:
    """
    Scans resume_text against the full skill vocabulary and returns every
    skill detected, in original casing (e.g. ["Python", "Pandas", "SQL"]).
    """
    vocabulary = _load_skill_vocabulary(csv_path)
    text_lower = resume_text.lower()

    detected = [skill for skill in vocabulary if _skill_present(skill, text_lower)]
    return detected