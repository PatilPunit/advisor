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
from skills_vocab import (
    load_master_vocabulary, find_skills_in_text,
    infer_all_mentioned_careers, strip_career_mentions, CAREER_NAMES,
)

# --------------------------------------------------------------------------
# Intent classification - this fixes the "same rigid pattern for every
# question" problem. A question like "what is a frontend developer" is
# INFORMATIONAL (wants an explanation), not a request for a personalized
# skill-match score. Previously, any question that happened to mention a
# career name (even via alias, e.g. "frontend") got routed through the
# grounded skill-match template regardless of what was actually being
# asked - producing confusing answers like "0% match, missing everything"
# for a simple definitional question. Now, informational questions get a
# genuinely open, conversational LLM response instead.
# --------------------------------------------------------------------------

_INFORMATIONAL_PATTERNS = [
    r"\bwhat is\b", r"\bwhat's\b", r"\bwhat are\b", r"\bwhat does\b",
    r"\bexplain\b", r"\btell me about\b", r"\bhow does\b", r"\bhow do\b",
    r"\bdefine\b", r"\bwho is\b", r"\bdescribe\b",
]
_COMPARISON_PATTERNS = [
    r"\bshould i\b", r"\bwhich is better\b", r"\bcompare\b", r"\bvs\b",
    r"\bversus\b", r"\bor should\b",
]


def _classify_intent(question: str) -> str:
    """Returns 'comparison', 'informational', or 'general'."""
    q_lower = question.lower()
    if any(re.search(p, q_lower) for p in _COMPARISON_PATTERNS):
        return "comparison"
    if any(re.search(p, q_lower) for p in _INFORMATIONAL_PATTERNS):
        return "informational"
    return "general"

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
    cleaned = strip_career_mentions(question)
    return find_skills_in_text(cleaned, vocab)


def _extract_mentioned_careers(question: str) -> List[str]:
    """Finds career names explicitly mentioned/described in the question."""
    return infer_all_mentioned_careers(question)


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


CAREER_DESCRIPTIONS = {
    "Data Scientist": "analyzes data to extract insights and build predictive models, typically using Python, SQL, and statistics.",
    "ML Engineer": "builds and deploys machine learning systems into production - training, scaling, and maintaining models that other software relies on.",
    "Data Analyst": "turns raw data into actionable business insights, often using SQL, Excel, and dashboarding tools like Power BI.",
    "Full Stack Developer": "builds both the frontend (what users see and interact with) and the backend (server logic, databases, APIs) of an application.",
    "Cyber Security Analyst": "protects systems and networks from threats - monitoring for suspicious activity, investigating incidents, and hardening defenses.",
    "Android Developer": "builds mobile applications for Android devices, typically using Kotlin or Java.",
    "Cloud Engineer": "designs, deploys, and manages infrastructure on cloud platforms like AWS, GCP, or Azure.",
    "AI Engineer": "designs and builds AI systems, often combining machine learning, deep learning, and production deployment.",
}


def _build_informational_fallback(mentioned_careers: List[str]) -> str:
    """Used only if Groq is unreachable for an informational question - still genuinely useful, not a dead end."""
    if mentioned_careers:
        career = mentioned_careers[0]
        description = CAREER_DESCRIPTIONS.get(career, "")
        return (
            f"A {career} {description}\n\n"
            f"If you'd like, tell me your current skills (e.g. \"I know Python and SQL\") "
            f"and I can show you exactly how close you are to this path."
        )
    return (
        "I'm having trouble reaching my reasoning engine right now - try again in a moment. "
        f"In the meantime, feel free to ask about any of these paths: {', '.join(CAREER_NAMES)}."
    )


def _build_llm_prompt(question: str, intent: str, facts: Dict, mentioned_careers: List[str], conversation_history: Optional[List[Dict]] = None) -> str:
    history_block = ""
    if conversation_history:
        turns = [f"Student asked: {t['question']}\nYou answered: {t['answer']}" for t in conversation_history[-4:]]
        history_block = "Previous conversation:\n" + "\n\n".join(turns) + "\n\n"

    if intent == "informational":
        career_hint = f" (they seem to be asking about {mentioned_careers[0]})" if mentioned_careers else ""
        skill_hint = ""
        if facts and facts.get("has_facts"):
            skill_hint = (
                f"\n\n(For context if relevant: they know {facts['possessed_skills'] or 'no listed skills yet'}. "
                f"Only mention this if it naturally fits the answer - the question is asking for an explanation, "
                f"not a skill-match score.)"
            )
        return f"""{history_block}The student's question{career_hint}: "{question}"

This is an informational/explanatory question - answer it directly and clearly, like a knowledgeable mentor would (what the role involves, what a beginner should know, etc.). Do NOT respond with a rigid "X% match" skill-comparison format - that's not what's being asked. Keep it conversational, 3-5 sentences.{skill_hint}"""

    if facts and facts.get("has_facts"):
        return f"""{history_block}The student's new question: "{question}"

Ground truth facts you MUST use (do not invent any numbers, skills, or project names beyond these):
- Best-fit career: {facts['recommended_career']}
- Skill match: {facts['match_percent']:.0f}%
- Skills they already have: {facts['possessed_skills'] or 'none yet'}
- Skills they're missing: {facts['missing_skills'] or 'none - fully ready'}
- Suggested starter project: {facts['suggested_project']}

Write a natural, encouraging, conversational reply (3-5 sentences). Reference the specific facts above naturally in your own words - don't just restate them as a list. End with one concrete, motivating next step. Do not mention any career, skill, or percentage that isn't in the facts above."""

    return f"""{history_block}The student's new question: "{question}"

You don't have specific skill data for this student yet. Answer their question helpfully and conversationally as a knowledgeable career mentor would. Keep it to 3-5 sentences. If natural, invite them to share their current skills for a personalized match - but don't force it."""


def answer_career_question(
    question: str,
    user_skills: Optional[List[str]] = None,
    conversation_history: Optional[List[Dict]] = None,
) -> Dict:
    """
    Main entry point. Classifies intent first:
      - "informational" (what/explain/how/define) -> open explanatory answer,
        never forced into the rigid skill-match template
      - "comparison" or "general" -> grounded skill-match facts used when
        skills are available

    ALWAYS attempts the LLM - only falls back to a deterministic answer
    (still genuinely useful, not just an error) if Groq is unreachable.
    """
    intent = _classify_intent(question)
    facts = _gather_grounded_facts(question, user_skills)
    mentioned_careers = facts.get("mentioned_careers", [])

    prompt = _build_llm_prompt(question, intent, facts, mentioned_careers, conversation_history)
    llm_answer = call_groq(prompt)

    if llm_answer:
        answer = llm_answer
    elif intent == "informational":
        answer = _build_informational_fallback(mentioned_careers)
    else:
        answer = facts["fallback_answer"]

    return {
        "answer": answer,
        "recommended_career": facts["recommended_career"],
        "possessed_skills": facts["possessed_skills"],
        "missing_skills": facts["missing_skills"],
        "suggested_project": facts["suggested_project"],
    }