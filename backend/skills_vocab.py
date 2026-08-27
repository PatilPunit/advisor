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
CAREER_PATHS_CSV = os.path.join("/home/punit/Downloads/Mint/AI_career_advisor/dataset/career_paths.csv")

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


# --------------------------------------------------------------------------
# Career inference - shared between the AI Mentor and the Job Matching
# engine, so both detect careers from free text the same consistent way.
# --------------------------------------------------------------------------

CAREER_NAMES = [
    "Data Scientist", "ML Engineer", "Data Analyst", "Full Stack Developer",
    "Cyber Security Analyst", "Android Developer", "Cloud Engineer", "AI Engineer",
]

# Common alternate phrasings (and common typos) mapped to the canonical
# career name. Substring/alias matching only - deliberately NOT character-
# level fuzzy matching, which previously produced false positives (e.g.
# "I know Python" incorrectly matching "AI Engineer" on coincidental
# letter overlap with zero real semantic connection).
CAREER_ALIASES = {
    "Data Scientist": ["data science"],
    "ML Engineer": ["machine learning engineer", "machine learning", " ml "],
    "Data Analyst": ["data analytics", "data analysis"],
    "Full Stack Developer": [
        "full stack", "fullstack", "web developer", "web development",
        "frontend developer", "front end developer", "front-end developer",
        "fronend developer", "fronend", "frontend", "backend developer", "backend",
    ],
    "Cyber Security Analyst": [
        "cybersecurity", "cyber security", "security analyst", "security engineer",
        "security breaches", "defensive controls", "monitoring for threats",
        "protects computer networks",
    ],
    "Android Developer": ["android development", "android app"],
    "Cloud Engineer": ["cloud computing", "devops"],
    "AI Engineer": ["artificial intelligence engineer", "artificial intelligence"],
}


def infer_all_mentioned_careers(text: str) -> List[str]:
    """
    Returns every career mentioned/described in a piece of free text, using
    substring + alias matching. Used by the AI Mentor (to detect which
    career a question is about) and the Job Matching engine (to infer a
    role from a job description written in plain English without naming
    specific tools - e.g. "monitors for threats, investigates security
    breaches" clearly describes a Cyber Security Analyst role even
    without the literal word "Linux" or "SIEM" appearing anywhere).
    """
    text_padded = f" {text.lower()} "
    found = []
    for career in CAREER_NAMES:
        phrases = [career.lower()] + CAREER_ALIASES.get(career, [])
        if any(phrase in text_padded for phrase in phrases) and career not in found:
            found.append(career)
    return found


def strip_career_mentions(text: str) -> str:
    """
    Removes career name/alias phrases from text (case-insensitively),
    leaving everything else intact. Used before skill extraction so that
    a career being DISCUSSED (e.g. "ML Engineering") doesn't get
    misread as a skill the person claims to POSSESS just because it
    happens to contain a skill-like abbreviation (e.g. "ML").
    """
    result = text
    all_phrases = list(CAREER_NAMES)
    for aliases in CAREER_ALIASES.values():
        all_phrases.extend(aliases)
    # Longest phrases first, so "ML Engineer" is stripped before a bare "ML" could be
    for phrase in sorted(all_phrases, key=len, reverse=True):
        result = re.sub(re.escape(phrase), " ", result, flags=re.IGNORECASE)
    return result