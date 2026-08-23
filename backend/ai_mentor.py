"""
ai_mentor.py
--------------
The "AI Mentor" - answers free-text career questions using a hosted LLM
(Groq, free tier) grounded in real data from your recommender.

ARCHITECTURE (read this before changing anything):
  1. Parse the question for mentioned skills/careers, call recommend_career()
     to get REAL facts when skills are available (never invented, never
     hallucinated - this part is 100% deterministic).
  2. ALWAYS attempt to call Groq for the actual reply - even for general
     questions with no specific skills mentioned (e.g. "what does a
     frontend developer do?"). Previously this codebase short-circuited
     and returned a canned message for any question without detected
     skills, which is why the chatbot felt "static" - it never even
     tried reaching the LLM for a huge class of normal questions. Fixed.
  3. Only fall back to a deterministic templated answer if Groq is
     genuinely unreachable (missing key, network error, bad response) -
     and that failure is now LOUDLY logged to your terminal, not silently
     swallowed, so you can actually see why it failed.
"""

from __future__ import annotations

import os
import re
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv

# Loads variables from a .env file sitting next to this file (backend/.env)
# directly into the environment. This bypasses the entire "did I export
# this in the right terminal / did .bashrc actually get sourced" problem -
# it's read fresh from a file on every single process start, no matter
# which terminal, IDE, or shell launches uvicorn.
load_dotenv()

from recommender import recommend_career
from project import get_project_details
from skills_vocab import load_master_vocabulary, find_skills_in_text

CAREER_NAMES = [
    "Data Scientist", "ML Engineer", "Data Analyst", "Full Stack Developer",
    "Cyber Security Analyst", "Android Developer", "Cloud Engineer", "AI Engineer",
]

# Common alternate phrasings (and common typos) mapped to the canonical
# career name. Substring/alias matching only - deliberately NOT using
# character-level fuzzy matching, since that previously produced false
# positives (e.g. "I know Python" incorrectly matching "AI Engineer" on
# coincidental letter overlap with zero real semantic connection).
CAREER_ALIASES = {
    "Data Scientist": ["data science"],
    "ML Engineer": ["machine learning engineer", "machine learning", " ml "],
    "Data Analyst": ["data analytics", "data analysis"],
    "Full Stack Developer": [
        "full stack", "fullstack", "web developer", "web development",
        "frontend developer", "front end developer", "front-end developer",
        "fronend developer", "fronend", "frontend", "backend developer", "backend",
    ],
    "Cyber Security Analyst": ["cybersecurity", "cyber security", "security analyst", "security engineer"],
    "Android Developer": ["android development", "android app"],
    "Cloud Engineer": ["cloud computing", "devops"],
    "AI Engineer": ["artificial intelligence engineer", "artificial intelligence"],
}

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"  # swap to "llama-3.1-8b-instant" for even faster, slightly less capable
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if GROQ_API_KEY:
    print(f"[ai_mentor] GROQ_API_KEY loaded ({len(GROQ_API_KEY)} chars) - mentor will use live LLM.")
else:
    print("[ai_mentor] GROQ_API_KEY NOT found. Create backend/.env with GROQ_API_KEY=your_key - mentor will use templated fallback only until then.")


def call_groq(prompt: str, timeout: int = 20) -> Optional[str]:
    """
    Calls Groq's hosted LLM API. Returns the generated text, or None if it
    can't be reached - and in every failure case, prints EXACTLY why to
    the terminal, instead of silently swallowing the error. This is the
    difference between "it just doesn't work" and "oh, it's a 401, my key
    is wrong" - always check your terminal output after a failed chat.
    """
    if not GROQ_API_KEY:
        print("[ai_mentor] Skipping Groq call - GROQ_API_KEY not set.")
        return None

    try:
        response = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a warm, knowledgeable AI career mentor for a "
                            "computer engineering student. You help with career "
                            "choice, skill planning, and general tech career questions."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
                "max_tokens": 400,
            },
            timeout=timeout,
        )
    except requests.exceptions.RequestException as e:
        print(f"[ai_mentor] Groq request FAILED (network/connection error): {e}")
        return None

    if response.status_code != 200:
        print(f"[ai_mentor] Groq returned HTTP {response.status_code}: {response.text[:500]}")
        return None

    try:
        data = response.json()
        text = data["choices"][0]["message"]["content"].strip()
        if not text:
            print("[ai_mentor] Groq returned an empty response.")
            return None
        return text
    except (KeyError, IndexError, ValueError) as e:
        print(f"[ai_mentor] Could not parse Groq response ({e}): {response.text[:500]}")
        return None


def _extract_mentioned_skills(question: str) -> List[str]:
    vocab = load_master_vocabulary()
    return find_skills_in_text(question, vocab)


def _extract_mentioned_careers(question: str) -> List[str]:
    """
    Finds career names explicitly mentioned in the question, using exact
    substring + curated alias matching (e.g. "Data Science" matches "Data
    Scientist", "ML" matches "ML Engineer", "frontend" matches "Full Stack
    Developer"). Careers not present in this system are simply not
    detected - the mentor still answers using whatever it did find, or
    falls back to general advice if nothing matched.
    """
    q_padded = f" {question.lower()} "
    found = []
    for career in CAREER_NAMES:
        all_phrases = [career.lower()] + CAREER_ALIASES.get(career, [])
        if any(phrase in q_padded for phrase in all_phrases) and career not in found:
            found.append(career)
    return found


def generate_advice(skills: List[str], career: str) -> Dict:
    """Given known skills and ONE target career, returns structured advice."""
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
    """Returns the ordered list of skills still needed for `career`."""
    from roadmap import get_roadmap
    known_lower = {s.lower() for s in skills}
    return [s for s in get_roadmap(career) if s.lower() not in known_lower]


def _gather_grounded_facts(question: str, user_skills: Optional[List[str]] = None) -> Dict:
    """
    Deterministic fact-gathering. Returns has_facts=False when no skills
    are mentioned/known - that's now just informational, NOT a reason to
    skip the LLM (see answer_career_question below).
    """
    mentioned_skills_in_question = _extract_mentioned_skills(question)
    mentioned_careers = _extract_mentioned_careers(question)
    effective_skills = list(set((user_skills or []) + mentioned_skills_in_question))

    if not effective_skills:
        return {
            "has_facts": False,
            "recommended_career": None,
            "possessed_skills": [],
            "missing_skills": [],
            "suggested_project": None,
            "match_percent": 0,
            "mentioned_careers": mentioned_careers,
            "fallback_answer": (
                "I couldn't detect any specific skills in your message. "
                "Try something like: \"I know Python and SQL. Should I learn "
                "Data Engineering or Data Science?\" - or just ask me anything "
                "about tech careers in general."
            ),
        }

    if len(mentioned_careers) >= 2:
        candidates = [generate_advice(effective_skills, c) for c in mentioned_careers]
        best = max(candidates, key=lambda c: c["match_percent"])
    elif len(mentioned_careers) == 1:
        best = generate_advice(effective_skills, mentioned_careers[0])
    else:
        results = recommend_career(effective_skills, None, top_n=1)
        top = results[0]
        best = {
            "career": top["career"], "match_percent": top["match_percent"],
            "possessed_skills": top["matched_skills"], "missing_skills": top["missing_skills"],
            "suggested_project": top.get("beginner_project"),
        }

    missing_str = ", ".join(best["missing_skills"]) if best["missing_skills"] else "nothing - fully ready"
    possessed_str = ", ".join(best["possessed_skills"]) if best["possessed_skills"] else "none yet"
    fallback_answer = (
        f"Based on your skills, {best['career']} is a strong fit "
        f"({best['match_percent']:.0f}% match).\n\n"
        f"You already possess: {possessed_str}\n"
        f"Missing: {missing_str}\n"
        f"Suggested Project: {best['suggested_project']}"
    )

    return {
        "has_facts": True,
        "recommended_career": best["career"],
        "possessed_skills": best["possessed_skills"],
        "missing_skills": best["missing_skills"],
        "suggested_project": best["suggested_project"],
        "match_percent": best["match_percent"],
        "mentioned_careers": mentioned_careers,
        "fallback_answer": fallback_answer,
    }


def _build_llm_prompt(question: str, facts: Dict, conversation_history: Optional[List[Dict]] = None) -> str:
    history_block = ""
    if conversation_history:
        turns = [f"Student asked: {t['question']}\nYou answered: {t['answer']}" for t in conversation_history[-4:]]
        history_block = "Previous conversation:\n" + "\n\n".join(turns) + "\n\n"

    if facts["has_facts"]:
        return f"""{history_block}The student's new question: "{question}"

Ground truth facts you MUST use (do not invent any numbers, skills, or project names beyond these):
- Best-fit career: {facts['recommended_career']}
- Skill match: {facts['match_percent']:.0f}%
- Skills they already have: {facts['possessed_skills'] or 'none yet'}
- Skills they're missing: {facts['missing_skills'] or 'none - fully ready'}
- Suggested starter project: {facts['suggested_project']}

Write a natural, encouraging, conversational reply (3-5 sentences). Reference the specific facts above naturally in your own words - don't just restate them as a list. End with one concrete, motivating next step. Do not mention any career, skill, or percentage that isn't in the facts above."""

    # No specific skills detected - still a real question, still gets a
    # real dynamic answer, just without invented match percentages.
    return f"""{history_block}The student's new question: "{question}"

You don't have specific skill data for this student yet. Answer their question helpfully and conversationally as a knowledgeable career mentor would - general advice, explanations of roles, encouragement, whatever fits the question. Keep it to 3-5 sentences. If it's natural to do so, invite them to share their current skills (e.g. "I know Python and SQL") so you can give them a personalized match next time - but don't force this if it doesn't fit the question."""


def answer_career_question(
    question: str,
    user_skills: Optional[List[str]] = None,
    conversation_history: Optional[List[Dict]] = None,
) -> Dict:
    """
    Main entry point. ALWAYS attempts the LLM first (grounded with real
    facts when available, general-purpose when not) - only falls back to
    a fixed templated answer if Groq is genuinely unreachable.
    """
    facts = _gather_grounded_facts(question, user_skills)
    prompt = _build_llm_prompt(question, facts, conversation_history)
    llm_answer = call_groq(prompt)

    return {
        "answer": llm_answer if llm_answer else facts["fallback_answer"],
        "recommended_career": facts["recommended_career"],
        "possessed_skills": facts["possessed_skills"],
        "missing_skills": facts["missing_skills"],
        "suggested_project": facts["suggested_project"],
    }