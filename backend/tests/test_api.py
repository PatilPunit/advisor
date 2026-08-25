"""
tests/test_api.py
--------------------
End-to-end API integration tests - the "does the whole system actually
work together" tests, not just individual functions in isolation.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_home_route(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["message"] == "AI Career Advisor Running"


def test_recommend_endpoint_matches_spec_example(client):
    r = client.post("/recommend", json={"skills": ["Python", "Pandas"], "interest": None})
    assert r.status_code == 200
    assert r.json()["career"] == "Data Scientist"
    assert r.json()["match_score"] == 40.0


def test_recommend_rejects_empty_skills(client):
    r = client.post("/recommend", json={"skills": []})
    assert r.status_code == 400


def test_full_user_journey(client):
    """Register -> login -> set goal -> mark skill complete -> dashboard reflects it."""
    r = client.post("/register", json={"name": "Jarad", "email": "jarad@t.com", "password": "pw123456"})
    uid = r.json()["id"]

    login = client.post("/login", json={"email": "jarad@t.com", "password": "pw123456"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client.post(f"/users/{uid}/goal", json={"career": "Data Scientist"})
    client.post(f"/users/{uid}/skills", json={"skill_name": "Python", "completed": True})

    r = client.get(f"/dashboard/{uid}", headers=headers)
    assert r.status_code == 200
    assert r.json()["completed_skills"] == 1