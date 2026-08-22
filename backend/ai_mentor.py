"""
ai_mentor.py
--------------
The "AI Mentor" - answers free-text career questions.

IMPORTANT - honest disclosure: this is a rule-based reasoning engine, not a
live LLM. It parses the question for mentioned skills and careers using the
same matching logic as the resume extractor, then reuses recommend_career()
to produce a grounded, data-backed answer - no hallucinated skill gaps.

It's built with a single entry point (answer_career_question) so you can
later swap the reasoning step for a real LLM call (e.g. Anthropic/OpenAI
API) without changing anything else that calls it - the interface would
stay identical: question in, structured answer out.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from recommender import recommend_career
from project import get_project_details
from skills_vocab import load_master_vocabulary, find_skills_in_text

CAREER_NAMES = [
    "Data Scientist", "ML Engineer", "Data Analyst", "Full Stack Developer",
    "Cyber Security Analyst", "Android Developer", "Cloud Engineer", "AI Engineer",
]


def _extract_mentioned_skills(question: str) -> List[str]:
    vocab = load_master_vocabulary()
    return find_skills_in_text(question, vocab)


import difflib


def _extract_mentioned_careers(question: str) -> List[str]:
    """
    Finds career names mentioned in the question, tolerant of loose phrasing
    (e.g. "Data Science" correctly matches "Data Scientist"). Careers not
    present in this system (e.g. "Data Engineering", which isn't one of the
    8 careers in career_paths.csv) are simply not detected - the mentor
    still answers using whichever recognized career(s) it did find.
    """
    # Split the question into candidate phrases on common separators
    raw_phrases = re.split(r"[,.!?]|(?:\bor\b)|(?:\band\b)", question, flags=re.IGNORECASE)
    candidates = [p.strip() for p in raw_phrases if p.strip()]

    found = []
    for phrase in candidates:
        phrase_lower = phrase.lower()
        best_career, best_ratio = None, 0.0
        for career in CAREER_NAMES:
            career_lower = career.lower()
            # exact substring (either direction) counts as a strong match
            if career_lower in phrase_lower or phrase_lower in career_lower:
                best_career, best_ratio = career, 1.0
                break
            ratio = difflib.SequenceMatcher(None, phrase_lower, career_lower).ratio()
            if ratio > best_ratio:
                best_career, best_ratio = career, ratio
        if best_career and best_ratio >= 0.55 and best_career not in found:
            found.append(best_career)

    return found


def generate_advice(skills: List[str], career: str) -> Dict:
    """
    Given known skills and ONE target career, returns a structured advice
    block: possessed skills, missing skills, match %, and a suggested
    beginner project.
    """
    results = recommend_career(skills, career, top_n=8)
    match = next((r for r in results if r["career"].lower() == career.lower()), results[0])

    beginner_project = match.get("beginner_project", "")
    project_details = get_project_details(beginner_project) if beginner_project else None

    return {
        "career": match["career"],
        "match_percent": match["match_percent"],
        "possessed_skills": match["matched_skills"],
        "missing_skills": match["missing_skills"],
        "suggested_project": project_details["project_name"] if project_details else beginner_project,
    }


def generate_learning_plan(skills: List[str], career: str) -> List[str]:
    """Returns the ordered list of skills still needed for `career`, given `skills` already known."""
    from roadmap import get_roadmap
    known_lower = {s.lower() for s in skills}
    full_roadmap = get_roadmap(career)
    return [s for s in full_roadmap if s.lower() not in known_lower]


def answer_career_question(question: str, user_skills: Optional[List[str]] = None) -> Dict:
    """
    Main entry point for the mentor. Parses the question, figures out what
    it's really asking, and returns a structured answer.

    Handles two shapes well:
      1. "I know X and Y. Should I learn A or B?" -> comparison between two careers
      2. "Should I learn ML?" / general question mentioning one career or skill
    """
    mentioned_skills_in_question = _extract_mentioned_skills(question)
    mentioned_careers = _extract_mentioned_careers(question)

    # Skills can come from the question itself ("I know Python and SQL")
    # or be passed in explicitly (e.g. from a logged-in user's profile)
    effective_skills = list(set((user_skills or []) + mentioned_skills_in_question))

    if not effective_skills:
        return {
            "answer": (
                "I couldn't detect any specific skills in your message. "
                "Try something like: \"I know Python and SQL. Should I learn "
                "Data Engineering or Data Science?\""
            ),
            "recommended_career": None,
            "possessed_skills": [],
            "missing_skills": [],
            "suggested_project": None,
        }

    # Case 1: comparing two (or more) specific careers
    if len(mentioned_careers) >= 2:
        candidates = [generate_advice(effective_skills, c) for c in mentioned_careers]
        best = max(candidates, key=lambda c: c["match_percent"])

        missing_str = ", ".join(best["missing_skills"]) if best["missing_skills"] else "nothing - you're fully ready!"
        possessed_str = ", ".join(best["possessed_skills"]) if best["possessed_skills"] else "none yet"

        answer = (
            f"Based on your skills, {best['career']} is closer "
            f"({best['match_percent']:.0f}% match).\n\n"
            f"You already possess: {possessed_str}\n"
            f"Missing: {missing_str}\n"
            f"Suggested Project: {best['suggested_project']}"
        )

        return {
            "answer": answer,
            "recommended_career": best["career"],
            "possessed_skills": best["possessed_skills"],
            "missing_skills": best["missing_skills"],
            "suggested_project": best["suggested_project"],
        }

    # Case 2: exactly one career mentioned - direct advice on that path
    if len(mentioned_careers) == 1:
        advice = generate_advice(effective_skills, mentioned_careers[0])
        missing_str = ", ".join(advice["missing_skills"]) if advice["missing_skills"] else "nothing - you're fully ready!"
        possessed_str = ", ".join(advice["possessed_skills"]) if advice["possessed_skills"] else "none yet"

        answer = (
            f"Based on your skills, {advice['career']} is a strong fit "
            f"({advice['match_percent']:.0f}% match).\n\n"
            f"You already possess: {possessed_str}\n"
            f"Missing: {missing_str}\n"
            f"Suggested Project: {advice['suggested_project']}"
        )
        return {
            "answer": answer,
            "recommended_career": advice["career"],
            "possessed_skills": advice["possessed_skills"],
            "missing_skills": advice["missing_skills"],
            "suggested_project": advice["suggested_project"],
        }

    # Case 3: no specific career named - recommend the best overall fit
    results = recommend_career(effective_skills, None, top_n=1)
    top = results[0]
    missing_str = ", ".join(top["missing_skills"]) if top["missing_skills"] else "nothing - you're fully ready!"
    possessed_str = ", ".join(top["matched_skills"]) if top["matched_skills"] else "none yet"

    answer = (
        f"Based on the skills you mentioned, {top['career']} looks like your strongest fit "
        f"({top['match_percent']:.0f}% match).\n\n"
        f"You already possess: {possessed_str}\n"
        f"Missing: {missing_str}"
    )

    return {
        "answer": answer,
        "recommended_career": top["career"],
        "possessed_skills": top["matched_skills"],
        "missing_skills": top["missing_skills"],
        "suggested_project": top.get("beginner_project"),
    }