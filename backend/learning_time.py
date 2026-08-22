"""
learning_time.py
-------------------
Deliverable 7: Learning Time Predictor.

Estimates how long it will take a user to become job-ready for a target
career, based on how many roadmap skills they're still missing.

The per-skill time estimate is a heuristic, not a scientific model - it's
based on typical time-to-competency for a single skill/tool at a
beginner-to-working level (not mastery), assuming consistent practice.
Tune WEEKS_PER_SKILL / WEEKLY_HOURS below to match your own experience.
"""

from __future__ import annotations

from typing import Dict, List

from roadmap import generate_dynamic_roadmap

WEEKS_PER_SKILL = 3
WEEKLY_HOURS = 15

# "Difficulty" here means the intrinsic difficulty of the CAREER PATH itself
# (how deep and broad the field is), not how far along the user is - a
# beginner aiming at AI Engineer still faces an "Advanced" path either way.
CAREER_DIFFICULTY = {
    "data scientist": "Intermediate",
    "ml engineer": "Intermediate",
    "data analyst": "Beginner",
    "full stack developer": "Beginner",
    "cyber security analyst": "Intermediate",
    "android developer": "Beginner",
    "cloud engineer": "Intermediate",
    "ai engineer": "Advanced",
}


def estimate_learning_time(career: str, current_skills: List[str]) -> Dict:
    """
    Args:
        career: target career, e.g. "ML Engineer"
        current_skills: skills the user already has

    Returns:
        {
          "estimated_duration": "6 Months",
          "weekly_hours": 15,
          "difficulty": "Intermediate",
          "remaining_skills": [...],
        }
    """
    remaining = generate_dynamic_roadmap(career, current_skills)

    total_weeks = len(remaining) * WEEKS_PER_SKILL
    months = round(total_weeks / 4.33, 1)

    difficulty = CAREER_DIFFICULTY.get(career.strip().lower(), "Intermediate")

    if months >= 1:
        duration_str = f"{months} Months" if months != 1 else "1 Month"
    else:
        duration_str = f"{total_weeks} Weeks"

    return {
        "estimated_duration": duration_str,
        "weekly_hours": WEEKLY_HOURS,
        "difficulty": difficulty,
        "remaining_skills": remaining,
    }