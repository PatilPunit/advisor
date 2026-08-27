"""
tests/test_mentor.py
------------------------
Tests for the AI Mentor - intent classification and grounded fact-gathering.
Deliberately does NOT test live Groq output (that's non-deterministic and
network-dependent) - tests the deterministic parts: intent routing, skill
extraction, and the fallback answer path (which always runs when no
GROQ_API_KEY is set, exactly like these tests run).
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_mentor import answer_career_question, _classify_intent, _extract_mentioned_skills


def test_comparison_intent_detected():
    assert _classify_intent("Should I learn Python or SQL?") == "comparison"


def test_informational_intent_detected():
    assert _classify_intent("What is a frontend developer?") == "informational"


def test_general_intent_when_neither_matches():
    assert _classify_intent("Python Pandas SQL") == "general"


def test_skill_extraction_finds_real_skills():
    skills = _extract_mentioned_skills("I know Python and SQL")
    print(skills)
    assert "Python" in skills
    assert "SQL" in skills
    



def test_career_mentioned_in_question_not_credited_as_skill():
    """Regression test: 'ML Engineering' (a career) shouldn't be miscounted as knowing 'ML'."""
    skills = _extract_mentioned_skills("Should I learn ML Engineering?")
    assert "ML" not in skills


def test_informational_question_does_not_use_rigid_skill_template():
    """
    Regression test for the 'static chatbot' bug: an informational question
    must not get the grounded match-percent template as its primary framing.
    """
    result = answer_career_question("what is a frontend developer", user_skills=["Python"])
    assert "% match" not in result["answer"]


def test_comparison_question_with_no_groq_falls_back_to_grounded_template():
    """With no GROQ_API_KEY set (true in this test environment), comparison
    questions should still produce a real, data-grounded answer."""
    result = answer_career_question("I know Python and SQL. Should I learn Data Science or ML Engineering?")
    assert result["recommended_career"] == "Data Scientist"
    assert "Python" in result["possessed_skills"]
    assert "SQL" in result["possessed_skills"]