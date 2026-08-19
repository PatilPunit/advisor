"""
roadmap.py
-----------
Skill roadmap engine for the Career Path Advisor project.

Reads dataset/skill_roadmap.csv and returns the ordered list of skills
a user should learn for a given career.

Usage:
    from roadmap import get_roadmap, print_roadmap

    steps = get_roadmap("Data Scientist")
    print(steps)          # ['Python', 'NumPy', 'Pandas', ...]

    print_roadmap("Data Scientist")
    # 1. Python
    # 2. NumPy
    # ...
"""

from __future__ import annotations

import csv
import difflib
import os
from typing import List, Optional


# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROADMAP_CSV = os.path.join("/home/punit/Downloads/Mint/AI_career_advisor/dataset/skill_roadmap.csv")

FUZZY_MATCH_THRESHOLD = 0.8  # for tolerant career-name lookup (typos, casing)


# --------------------------------------------------------------------------
# Internal helpers
# --------------------------------------------------------------------------

def _normalize(text: str) -> str:
    return text.strip().lower()


def _load_roadmap_data(csv_path: str = SKILL_ROADMAP_CSV) -> List[dict]:
    """
    Loads skill_roadmap.csv into a list of dicts:
    [{career, order(int), skill}, ...]
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"skill_roadmap.csv not found at: {csv_path}")

    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                order = int(row["order"])
            except (KeyError, ValueError):
                continue
            rows.append({
                "career": row["career"].strip(),
                "order": order,
                "skill": row["skill"].strip(),
            })
    return rows


def _resolve_career_name(career: str, all_careers: List[str]) -> Optional[str]:
    """
    Matches the requested career against known career names.
    Exact match (case-insensitive) first, then fuzzy fallback
    to tolerate typos like "Data Scientis".
    """
    career_n = _normalize(career)
    for c in all_careers:
        if _normalize(c) == career_n:
            return c

    # fuzzy fallback
    best_match, best_ratio = None, 0.0
    for c in all_careers:
        ratio = difflib.SequenceMatcher(None, career_n, _normalize(c)).ratio()
        if ratio > best_ratio:
            best_match, best_ratio = c, ratio

    return best_match if best_ratio >= FUZZY_MATCH_THRESHOLD else None


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------

def get_roadmap(career: str, csv_path: str = SKILL_ROADMAP_CSV) -> List[str]:
    """
    Returns the ordered list of skills for a given career.

    Args:
        career: career name, e.g. "Data Scientist"
        csv_path: override path to skill_roadmap.csv (mainly for testing)

    Returns:
        List of skill names in learning order, e.g.
        ["Python", "NumPy", "Pandas", "Statistics", "Machine Learning"]

    Raises:
        ValueError: if the career isn't found in the roadmap dataset.
    """
    rows = _load_roadmap_data(csv_path)
    all_careers = sorted({r["career"] for r in rows})

    resolved = _resolve_career_name(career, all_careers)
    if resolved is None:
        raise ValueError(
            f"No roadmap found for career '{career}'. "
            f"Available careers: {', '.join(all_careers)}"
        )

    career_rows = [r for r in rows if r["career"] == resolved]
    career_rows.sort(key=lambda r: r["order"])

    return [r["skill"] for r in career_rows]


def print_roadmap(career: str, csv_path: str = SKILL_ROADMAP_CSV) -> None:
    """Prints the roadmap as a numbered list, matching the expected output format."""
    skills = get_roadmap(career, csv_path)
    for i, skill in enumerate(skills, start=1):
        print(f"{i}. {skill}")


# --------------------------------------------------------------------------
# CLI demo / manual test
# --------------------------------------------------------------------------

if __name__ == "__main__":
    career = "Data Scientist"
    print(f"Roadmap for: {career}\n")
    print_roadmap(career)