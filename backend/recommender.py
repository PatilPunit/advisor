"""
recommender.py
---------------
Career recommendation engine for the Career Path Advisor project.

Reads dataset/career_paths.csv and scores every career against the
skills + interest supplied by the user, using a Skill Match %
(intersection of user skills vs required skills) with an optional
interest-relevance boost.

Usage:
    from recommender import recommend_career

    results = recommend_career(
        skills=["Python", "Pandas"],
        interest="data"
    )
    print(results[0])   # top match
"""

from __future__ import annotations

import csv
import difflib
import os
from dataclasses import dataclass, field
from typing import List, Optional


# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAREER_PATHS_CSV = "/home/punit/Downloads/Mint/AI_career_advisor/dataset/career_paths.csv"

# Below this similarity ratio, two skill strings are considered different
# (handles typos / minor variations like "JS" vs "Javascript" NOT matching
# unless close enough — tune as needed).
FUZZY_MATCH_THRESHOLD = 0.85


# --------------------------------------------------------------------------
# Data model
# --------------------------------------------------------------------------

@dataclass
class CareerMatch:
    career: str
    match_percent: float
    matched_skills: List[str]
    missing_skills: List[str]
    interest_score: float
    final_score: float
    beginner_project: str = ""
    advanced_project: str = ""

    def to_dict(self) -> dict:
        return {
            "career": self.career,
            "match_percent": round(self.match_percent, 2),
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
            "interest_score": round(self.interest_score, 2),
            "final_score": round(self.final_score, 2),
            "beginner_project": self.beginner_project,
            "advanced_project": self.advanced_project,
        }


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _normalize(text: str) -> str:
    """Lowercase + strip, used for consistent skill comparison."""
    return text.strip().lower()


def _load_career_data(csv_path: str = CAREER_PATHS_CSV) -> List[dict]:
    """
    Loads career_paths.csv into a list of dicts:
    [{career, required_skills(list), beginner_projects, advanced_projects}, ...]
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"career_paths.csv not found at: {csv_path}")

    careers = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            skills_raw = row["required_skills"]
            skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
            careers.append({
                "career": row["career"].strip(),
                "required_skills": skills,
                "beginner_projects": row.get("beginner_projects", "").strip(),
                "advanced_projects": row.get("advanced_projects", "").strip(),
            })
    return careers


def _skill_is_match(user_skill: str, required_skill: str) -> bool:
    """
    True if user_skill matches required_skill either exactly (case-insensitive)
    or is close enough via fuzzy matching (handles minor typos/variants).
    """
    u, r = _normalize(user_skill), _normalize(required_skill)
    if u == r:
        return True
    ratio = difflib.SequenceMatcher(None, u, r).ratio()
    return ratio >= FUZZY_MATCH_THRESHOLD


def _compute_skill_match(user_skills: List[str], required_skills: List[str]):
    """
    Compares user skills against a career's required skills.

    Returns:
        match_percent: float (0-100)
        matched: list of required skills the user already has
        missing: list of required skills the user still needs
    """
    if not required_skills:
        return 0.0, [], []

    matched, missing = [], []
    for req in required_skills:
        if any(_skill_is_match(u, req) for u in user_skills):
            matched.append(req)
        else:
            missing.append(req)

    match_percent = (len(matched) / len(required_skills)) * 100
    return match_percent, matched, missing


def _compute_interest_score(interest: Optional[str], career: str, required_skills: List[str]) -> float:
    """
    Simple interest relevance score (0-100) based on whether the interest
    keyword appears in the career name or its required skills.
    Returns 0 if no interest was supplied.
    """
    if not interest:
        return 0.0

    interest_n = _normalize(interest)
    haystack = _normalize(career) + " " + " ".join(_normalize(s) for s in required_skills)

    if interest_n in haystack:
        return 100.0

    # fuzzy fallback: check similarity against career name and each skill
    tokens = [career] + required_skills
    best_ratio = max(
        difflib.SequenceMatcher(None, interest_n, _normalize(t)).ratio()
        for t in tokens
    )
    return round(best_ratio * 100, 2)


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------

def recommend_career(
    skills: List[str],
    interest: Optional[str] = None,
    top_n: int = 3,
    skill_weight: float = 0.8,
    interest_weight: float = 0.2,
    csv_path: str = CAREER_PATHS_CSV,
) -> List[dict]:
    """
    Recommends the best-matching career(s) for a user.

    Args:
        skills: list of skills the user already has, e.g. ["Python", "Pandas"]
        interest: optional free-text interest, e.g. "data", "security", "web"
        top_n: how many top results to return
        skill_weight: weight given to skill match % in the final score (0-1)
        interest_weight: weight given to interest relevance in final score (0-1)
        csv_path: override path to career_paths.csv (mainly for testing)

    Returns:
        A list of dicts (highest score first), each containing:
        career, match_percent, matched_skills, missing_skills,
        interest_score, final_score, beginner_project, advanced_project
    """
    if not skills:
        raise ValueError("skills list cannot be empty")

    careers = _load_career_data(csv_path)
    results: List[CareerMatch] = []

    for c in careers:
        match_percent, matched, missing = _compute_skill_match(skills, c["required_skills"])
        interest_score = _compute_interest_score(interest, c["career"], c["required_skills"])

        final_score = (match_percent * skill_weight) + (interest_score * interest_weight)

        results.append(CareerMatch(
            career=c["career"],
            match_percent=match_percent,
            matched_skills=matched,
            missing_skills=missing,
            interest_score=interest_score,
            final_score=final_score,
            beginner_project=c["beginner_projects"],
            advanced_project=c["advanced_projects"],
        ))

    # Rank by final_score, tie-break by match_percent
    results.sort(key=lambda r: (r.final_score, r.match_percent), reverse=True)

    return [r.to_dict() for r in results[:top_n]]


def recommend_top_career(skills: List[str], interest: Optional[str] = None) -> dict:
    """Convenience wrapper: returns only the single best-matching career."""
    ranked = recommend_career(skills, interest, top_n=1)
    return ranked[0] if ranked else {}


# --------------------------------------------------------------------------
# CLI demo / manual test
# --------------------------------------------------------------------------
"""
if __name__ == "__main__":
    demo_skills = ["Python", "Pandas"]
    demo_interest = "data"

    print(f"User skills: {demo_skills}")
    print(f"User interest: {demo_interest}\n")

    recommendations = recommend_career(demo_skills, demo_interest, top_n=5)

    for i, rec in enumerate(recommendations, start=1):
        print(f"#{i} {rec['career']}  —  Final Score: {rec['final_score']}%")
        print(f"    Skill Match: {rec['match_percent']}%  "
              f"(matched: {rec['matched_skills']} | missing: {rec['missing_skills']})")
        print(f"    Interest Relevance: {rec['interest_score']}%")
        print(f"    Suggested project: {rec['beginner_project']} -> {rec['advanced_project']}\n")
"""