"""
ai_mentor.py
--------------
The "AI Mentor" - answers free-text career questions.

Architecture: grounded RAG, not a blind chatbot. Before ever calling the
LLM, this still parses the question and calls recommend_career() to get
REAL facts (actual match %, actual missing skills, actual project names
from your CSVs). Those facts are then handed to a hosted LLM (via Groq)
as context, and the LLM's only job is to write a natural, warm, dynamic
response using them - it is instructed not to invent numbers or skills.

This means: the conversation genuinely varies response to response (real
LLM generation, not a template), while the facts stay 100% accurate,
because they never come from the LLM - only the phrasing does.

Why Groq instead of ChatGPT/Ollama:
  - Free tier, no credit card required
  - Hosted - nothing to install or run locally, no slow local inference
  - Extremely fast (Groq's custom LPU hardware, not GPUs - typically
    under a second per response)
  - One-time setup: sign up at console.groq.com, create an API key, set
    it as an environment variable. That's it.
  - If the API key is missing or the request fails, this module
    automatically falls back to the original rule-based templated answer -
    the app never breaks, it just becomes less conversational.
"""

from __future__ import annotations

import os
import re
from typing import Dict, List, Optional

import requests

from recommender import recommend_career
from project_bank import get_project_details
from skills_vocab import load_master_vocabulary, find_skills_in_text

CAREER_NAMES = [
    "Data Scientist", "ML Engineer", "Data Analyst", "Full Stack Developer",
    "Cyber Security Analyst", "Android Developer", "Cloud Engineer", "AI Engineer",
]

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"  # swap to "llama-3.1-8b-instant" for even faster, slightly less capable
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def call_groq(prompt: str, timeout: int = 20) -> Optional[str]:
    """
    Calls Groq's hosted, free LLM API. Returns the generated text, or None
    if the API key is missing / the request fails (caller should fall back
    to the deterministic templated answer).
    """
    if not GROQ_API_KEY:
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
                        "content": "You are a warm, direct AI career mentor for a computer engineering student.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
                "max_tokens": 400,
            },
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"].strip()
        return text if text else None
    except Exception:
        return None


def _extract_mentioned_skills(question: str) -> List[str]:
    vocab = load_master_vocabulary()
    return find_skills_in_text(question, vocab)


# Common alternate phrasings mapped to the canonical career name. Substring
# and alias matching only - NO character-level fuzzy matching, because
# short-string fuzzy ratios produce false positives (e.g. "I know Python"
# was previously matching "AI Engineer" purely on coincidental letter
# overlap, with no real semantic connection).
CAREER_ALIASES = {
    "Data Scientist": ["data science"],
    "ML Engineer": ["machine learning engineer", "machine learning", " ml "],
    "Data Analyst": ["data analytics", "data analysis"],
    "Full Stack Developer": ["full stack", "fullstack", "web developer", "web development"],
    "Cyber Security Analyst": ["cybersecurity", "cyber security", "security analyst", "security engineer"],
    "Android Developer": ["android development", "android app"],
    "Cloud Engineer": ["cloud computing", "devops"],
    "AI Engineer": ["artificial intelligence engineer", "artificial intelligence"],
}


def _extract_mentioned_careers(question: str) -> List[str]:
    """
    Finds career names explicitly mentioned in the question, using exact
    substring + curated alias matching only (e.g. "Data Science" matches
    "Data Scientist", "ML" matches "ML Engineer" when it appears as a
    standalone word). Careers not present in this system (e.g. "Data
    Engineering", which isn't one of the 8 careers in career_paths.csv) are
    simply not detected - the mentor still answers using whichever
    recognized career(s) it did find.
    """
    q_padded = f" {question.lower()} "  # padding lets " ml " match as a whole word
    found = []

    for career in CAREER_NAMES:
        career_lower = career.lower()
        aliases = CAREER_ALIASES.get(career, [])
        all_phrases = [career_lower] + aliases

        if any(phrase in q_padded for phrase in all_phrases) and career not in found:
            found.append(career)

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


def _gather_grounded_facts(question: str, user_skills: Optional[List[str]] = None) -> Dict:
    """
    Does all the REAL data work: parses the question, calls recommend_career(),
    and returns hard facts. Nothing here ever touches the LLM - this is the
    part that must never hallucinate.
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
            "fallback_answer": (
                "I couldn't detect any specific skills in your message. "
                "Try something like: \"I know Python and SQL. Should I learn "
                "Data Engineering or Data Science?\""
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
            "career": top["career"],
            "match_percent": top["match_percent"],
            "possessed_skills": top["matched_skills"],
            "missing_skills": top["missing_skills"],
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
        "fallback_answer": fallback_answer,
    }


def _build_llm_prompt(question: str, facts: Dict, conversation_history: Optional[List[Dict]] = None) -> str:
    history_block = ""
    if conversation_history:
        turns = []
        for turn in conversation_history[-4:]:  # last 4 turns for context, keeps prompt small
            turns.append(f"Student asked: {turn['question']}\nYou answered: {turn['answer']}")
        history_block = "Previous conversation:\n" + "\n\n".join(turns) + "\n\n"

    return f"""You are a warm, direct AI career mentor for a computer engineering student choosing between tech career paths. 

{history_block}The student's new question: "{question}"

Ground truth facts you MUST use (do not invent any numbers, skills, or project names beyond these):
- Best-fit career: {facts['recommended_career']}
- Skill match: {facts['match_percent']:.0f}%
- Skills they already have: {facts['possessed_skills'] or 'none yet'}
- Skills they're missing: {facts['missing_skills'] or 'none - fully ready'}
- Suggested starter project: {facts['suggested_project']}

Write a natural, encouraging, conversational reply (3-5 sentences). Reference the specific facts above naturally in your own words - don't just restate them as a list. If there's conversation history, acknowledge it like a real ongoing conversation. End with one concrete, motivating next step. Do not mention any career, skill, or percentage that isn't in the facts above."""


def answer_career_question(
    question: str,
    user_skills: Optional[List[str]] = None,
    conversation_history: Optional[List[Dict]] = None,
) -> Dict:
    """
    Main entry point for the mentor.

    Step 1 (always, deterministic): parse the question + call recommend_career()
    to get real, grounded facts - this never changes conversation to conversation.

    Step 2 (dynamic): hand those facts to a local LLM (Ollama) to write a
    genuinely varied, conversational response. If Ollama isn't running, falls
    back automatically to the deterministic templated answer from Step 1 - the
    mentor still works, just less conversationally, until Ollama is started.
    """
    facts = _gather_grounded_facts(question, user_skills)

    if not facts["has_facts"]:
        return {
            "answer": facts["fallback_answer"],
            "recommended_career": None,
            "possessed_skills": [],
            "missing_skills": [],
            "suggested_project": None,
        }

    prompt = _build_llm_prompt(question, facts, conversation_history)
    llm_answer = call_groq(prompt)

    return {
        "answer": llm_answer if llm_answer else facts["fallback_answer"],
        "recommended_career": facts["recommended_career"],
        "possessed_skills": facts["possessed_skills"],
        "missing_skills": facts["missing_skills"],
        "suggested_project": facts["suggested_project"],
    }