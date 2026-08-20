"""
project_bank.py
-----------------
Looks up project metadata (domain, difficulty) from dataset/project_bank.csv
for the beginner/advanced projects tied to a career in career_paths.csv.
"""

from __future__ import annotations

import csv
import os
from typing import List, Optional


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_BANK_CSV = os.path.join("/home/punit/Downloads/Mint/AI_career_advisor/dataset/project_bank.csv")


def _normalize(text: str) -> str:
    return text.strip().lower()


def _load_project_bank(csv_path: str = PROJECT_BANK_CSV) -> List[dict]:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"project_bank.csv not found at: {csv_path}")

    projects = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            projects.append({
                "project_name": row["project_name"].strip(),
                "domain": row["domain"].strip(),
                "difficulty": row["difficulty"].strip(),
            })
    return projects


def get_project_details(project_name: str, csv_path: str = PROJECT_BANK_CSV) -> Optional[dict]:
    """
    Returns {project_name, domain, difficulty} for a given project name,
    or a fallback dict with just the name if it's not found in project_bank.csv.
    """
    if not project_name:
        return None

    projects = _load_project_bank(csv_path)
    target = _normalize(project_name)

    for p in projects:
        if _normalize(p["project_name"]) == target:
            return p

    # Not found in project_bank.csv -> return name only, so the API never
    # silently drops a project just because the bank is incomplete.
    return {"project_name": project_name, "domain": None, "difficulty": None}


def get_projects_for_career(beginner_project: str, advanced_project: str) -> List[dict]:
    """
    Builds the ordered project list [beginner, advanced] with full details
    for the projects tied to a recommended career.
    """
    results = []
    for name in (beginner_project, advanced_project):
        details = get_project_details(name)
        if details:
            results.append(details)
    return results