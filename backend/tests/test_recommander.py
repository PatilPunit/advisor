"""
tests/test_recommender.py
----------------------------
Unit tests for the core career recommendation engine.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recommender import recommend_career


def test_python_pandas_recommends_data_scientist():
    """Spec's own worked example: Python + Pandas -> Data Scientist, 40% match."""
    results = recommend_career(["Python", "Pandas"], None, top_n=1)
    assert results[0]["career"] == "Data Scientist"
    assert results[0]["match_percent"] == 40.0


def test_missing_skills_are_correct():
    results = recommend_career(["Python", "Pandas"], None, top_n=1)
    missing = set(results[0]["missing_skills"])
    assert missing == {"SQL", "Statistics", "ML"}


def test_full_skill_match_gives_100_percent():
    results = recommend_career(
        ["Python", "SQL", "Pandas", "Statistics", "ML"], "Data Scientist", top_n=8
    )
    ds = next(r for r in results if r["career"] == "Data Scientist")
    assert ds["match_percent"] == 100.0
    assert ds["missing_skills"] == []


def test_empty_skills_list_raises():
    import pytest
    with pytest.raises(ValueError):
        recommend_career([], None)


def test_stated_interest_ranks_first_even_with_zero_skill_overlap():
    """Regression test: a user's stated career goal must outrank unrelated skill matches."""
    results = recommend_career(["Python", "Pandas"], "cybersecurity analyst", top_n=3)
    assert results[0]["career"] == "Cyber Security Analyst"


def test_case_insensitive_skill_matching():
    results = recommend_career(["python", "PANDAS"], None, top_n=1)
    assert results[0]["match_percent"] == 40.0