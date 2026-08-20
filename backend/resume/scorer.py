"""
resume/scorer.py
------------------
Scores a resume against a target career's required skills.

Formula: (detected / required) * 100
Example: 3 detected / 6 required -> 50%
"""

from __future__ import annotations

from typing import List, TypedDict


class ScoreResult(TypedDict):
    score: int
    matched: List[str]
    missing: List[str]


def calculate_score(detected_skills: List[str], required_skills: List[str]) -> ScoreResult:
    """
    Compares detected resume skills against a career's required skills.

    Args:
        detected_skills: skills found in the resume, e.g. ["Python", "Pandas", "SQL"]
        required_skills: skills required for the target career, e.g.
                          ["Python", "SQL", "Pandas", "Statistics", "ML"]

    Returns:
        {
          "score": 50,                  # rounded percentage
          "matched": ["Python", "SQL"], # required skills the resume has
          "missing": ["Statistics"],    # required skills the resume lacks
        }
    """
    if not required_skills:
        return {"score": 0, "matched": [], "missing": []}

    detected_lower = {s.lower() for s in detected_skills}

    matched = [s for s in required_skills if s.lower() in detected_lower]
    missing = [s for s in required_skills if s.lower() not in detected_lower]

    score = round((len(matched) / len(required_skills)) * 100)

    return {"score": score, "matched": matched, "missing": missing}