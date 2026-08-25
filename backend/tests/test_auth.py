"""
tests/test_auth.py
----------------------
Tests for Deliverable 6 (JWT) + Deliverable 7 (roles) - the highest-stakes
code in the project. These are the tests that must never be allowed to
regress silently.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_register_blocks_public_admin_escalation(client):
    r = client.post("/register", json={
        "name": "Hacker", "email": "hacker@test.com", "password": "pw123456", "role": "admin",
    })
    assert r.json()["role"] == "student"  # never "admin", regardless of what was requested


def test_login_returns_valid_jwt(client):
    client.post("/register", json={"name": "Alice", "email": "alice@t.com", "password": "pw123456"})
    r = client.post("/login", json={"email": "alice@t.com", "password": "pw123456"})
    assert r.json()["success"] is True
    assert r.json()["access_token"] is not None


def test_protected_route_rejects_missing_token(client):
    r1 = client.post("/register", json={"name": "Alice", "email": "alice2@t.com", "password": "pw123456"})
    user_id = r1.json()["id"]
    r = client.get(f"/dashboard/{user_id}")
    assert r.status_code == 401


def test_protected_route_blocks_cross_user_access(client):
    """The core IDOR fix: user A's valid token must never unlock user B's data."""
    r1 = client.post("/register", json={"name": "Alice", "email": "alice3@t.com", "password": "pw123456"})
    alice_id = r1.json()["id"]
    r2 = client.post("/register", json={"name": "Bob", "email": "bob3@t.com", "password": "pw123456"})
    bob_id = r2.json()["id"]

    login = client.post("/login", json={"email": "alice3@t.com", "password": "pw123456"})
    token = login.json()["access_token"]

    r = client.get(f"/dashboard/{bob_id}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_admin_only_route_blocks_students(client):
    r1 = client.post("/register", json={"name": "Alice", "email": "alice4@t.com", "password": "pw123456"})
    login = client.post("/login", json={"email": "alice4@t.com", "password": "pw123456"})
    token = login.json()["access_token"]

    r = client.get("/admin/analytics", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403