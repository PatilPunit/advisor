"""
job_match.py
--------------
Deliverable 4: Resume vs Job Matching.

Compares a resume's detected skills against a job description's detected
skills (keyword extraction), producing a match score, missing keywords,
and recommended next actions.
"""

from __future__ import annotations

from typing import Dict, List

from skills_vocab import load_master_vocabulary, find_skills_in_text


def extract_job_skills(job_description_text: str) -> List[str]:
    """Detects known skills/keywords mentioned in a job description."""
    vocab = load_master_vocabulary()
    return find_skills_in_text(job_description_text, vocab)


def match_resume_to_job(resume_skills: List[str], job_skills: List[str]) -> Dict:
    """
    Args:
        resume_skills: skills detected in the candidate's resume
        job_skills: skills detected in the job description

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