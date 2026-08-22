"""
resume/intelligence.py
-------------------------
Deliverable 3: Resume Intelligence Engine.

Goes beyond skill-matching (resume/scorer.py) to evaluate the resume's
STRUCTURE - things a recruiter notices in the first 10 seconds - and
produces a combined 0-100 score with concrete improvement suggestions.
"""

from __future__ import annotations

import re
from typing import Dict, List


def _has_github_link(text: str) -> bool:
    return bool(re.search(r"github\.com/\S+", text, re.IGNORECASE))


def _has_projects_section(text: str) -> bool:
    return bool(re.search(r"\bprojects?\b", text, re.IGNORECASE))


def _has_quantified_achievements(text: str) -> bool:
    """
    Looks for numbers paired with achievement language - e.g. "improved
    performance by 30%", "reduced load time by 2 seconds", "led a team of 5".
    A bare number alone (like a phone number or year) doesn't count.
    """
    patterns = [
        r"\d+%",                                  # "30%"
        r"\b(?:increased|improved|reduced|saved|grew|boosted|cut)\b[^.\n]{0,40}\d+",
        r"\bteam of \d+\b",
        r"\$\d+",                                 # dollar figures
    ]
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def _has_email(text: str) -> bool:
    return bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text))


def _has_linkedin(text: str) -> bool:
    return bool(re.search(r"linkedin\.com/in/\S+", text, re.IGNORECASE))


def evaluate_resume(resume_text: str, skill_match_percent: float) -> Dict:
    """
    Combines skill match (from scorer.py) with structural checks into one
    holistic score, plus a strengths/weaknesses breakdown.

    Weighting: 60% skill match, 40% structural completeness - a resume can
    have perfect skills but still lose points for missing a GitHub link,
    projects section, or quantified impact.
    """
    checks = {
        "GitHub Link": _has_github_link(resume_text),
        "Projects Section": _has_projects_section(resume_text),
        "Quantified Achievements": _has_quantified_achievements(resume_text),
        "Contact Email": _has_email(resume_text),
        "LinkedIn Profile": _has_linkedin(resume_text),
    }

    passed_checks = sum(1 for v in checks.values() if v)
    structure_score = (passed_checks / len(checks)) * 100

    overall_score = round((skill_match_percent * 0.6) + (structure_score * 0.4))

    weaknesses = [f"No {label}" for label, passed in checks.items() if not passed]
    strengths_structural = [label for label, passed in checks.items() if passed]

    return {
        "score": overall_score,
        "structure_checks": checks,
        "weaknesses": weaknesses,
        "structural_strengths": strengths_structural,
    }