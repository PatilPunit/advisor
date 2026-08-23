"""
job_match.py
--------------
Deliverable 4: Resume vs Job Matching.

Upgraded beyond simple keyword-matching: real job descriptions are often
written in plain English without naming specific tools ("monitors for
threats" instead of "SIEM", "Linux"). Pure keyword extraction fails on
these. This module now also INFERS the likely career/role from the JD's
overall language (reusing the same career-alias detection as the AI
Mentor) and, when direct keyword matches are sparse, falls back to that
career's actual required_skills from career_paths.csv as the implied
requirement set - so a vaguely-worded Cyber Security JD still produces a
meaningful match against Networking/Linux/Security, instead of an error.
"""

from __future__ import annotations

import csv
import os
import re
from typing import Dict, List, Optional

from skills_vocab import load_master_vocabulary, find_skills_in_text, infer_all_mentioned_careers

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAREER_PATHS_CSV = os.path.join(BASE_DIR, "dataset", "career_paths.csv")

_STOPWORDS = {
    "The", "We", "You", "Our", "This", "That", "Looking", "Must", "Should",
    "Will", "Job", "Role", "Position", "Company", "Team", "About", "Requirements",
    "Responsibilities", "Preferred", "Required", "Experience", "Years", "Strong",
    "Excellent", "Good", "Ability", "Knowledge", "Understanding", "Need", "Needs",
    "Want", "Wants", "Seeking", "Require", "Requires", "Ideal", "Candidate",
    "Skills", "Qualifications", "Plus", "Bonus", "Nice", "Success", "Field",
    "Combination", "Technical", "Operational", "Tool",
}


def _get_required_skills_for_career(career: str) -> List[str]:
    """Loads the required_skills list for a career directly from career_paths.csv."""
    if not os.path.exists(CAREER_PATHS_CSV):
        return []
    with open(CAREER_PATHS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["career"].strip().lower() == career.strip().lower():
                return [s.strip() for s in row["required_skills"].split(",") if s.strip()]
    return []


def extract_job_skills(job_description_text: str) -> Dict:
    """
    Detects skills/keywords in a job description using three layers:

      1. Direct vocabulary match (career_paths.csv skills + common tech terms)
      2. Fallback capitalized-word extraction (catches tools not in our
         vocabulary yet, e.g. "Terraform", "Snowflake")
      3. Domain inference: if the above two layers found fewer than 3
         concrete skills, infer the likely career from the JD's overall
         phrasing and merge in that career's real required_skills - this
         is what makes a plain-English JD like "monitors for threats,
         investigates security breaches" still produce a meaningful skill
         list, instead of returning almost nothing.

    Returns:
        {
          "skills": [...],           # final combined list used for matching
          "inferred_career": str|None,  # which career (if any) triggered layer 3
          "used_inference": bool,
        }
    """
    vocab = load_master_vocabulary()
    matched = find_skills_in_text(job_description_text, vocab)
    matched_lower = {m.lower() for m in matched}

    candidates = re.findall(r"\b[A-Z][a-zA-Z0-9+.#]{1,19}\b", job_description_text)
    extra = [
        c for c in dict.fromkeys(candidates)
        if c not in _STOPWORDS and c.lower() not in matched_lower
    ][:10]

    combined = matched + extra
    inferred_career = None
    used_inference = False

    if len(combined) < 3:
        mentioned_careers = infer_all_mentioned_careers(job_description_text)
        if mentioned_careers:
            inferred_career = mentioned_careers[0]
            implied_skills = _get_required_skills_for_career(inferred_career)
            combined_lower = {c.lower() for c in combined}
            for skill in implied_skills:
                if skill.lower() not in combined_lower:
                    combined.append(skill)
                    combined_lower.add(skill.lower())
            used_inference = True

    return {
        "skills": combined,
        "inferred_career": inferred_career,
        "used_inference": used_inference,
    }


def match_resume_to_job(resume_skills: List[str], job_skills: List[str]) -> Dict:
    """
    Args:
        resume_skills: skills detected in the candidate's resume
        job_skills: skills detected/inferred for the job description

    Returns:
        {
          "match_score": 82,
          "missing_keywords": ["Docker", "AWS", "TensorFlow"],
          "recommended_actions": ["Learn Docker", "Learn AWS", "Learn TensorFlow"],
        }
    """
    if not job_skills:
        return {"match_score": 0, "missing_keywords": [], "recommended_actions": []}

    resume_lower = {s.lower() for s in resume_skills}
    missing = [s for s in job_skills if s.lower() not in resume_lower]
    matched_count = len(job_skills) - len(missing)
    match_score = round((matched_count / len(job_skills)) * 100)

    recommended_actions = [f"Learn {skill}" for skill in missing[:5]]
    if len(missing) > 5:
        recommended_actions.append(f"...and {len(missing) - 5} more")

    return {
        "match_score": match_score,
        "missing_keywords": missing,
        "recommended_actions": recommended_actions,
    }