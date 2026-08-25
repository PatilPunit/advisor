"""
auth.py
---------
Deliverable 6: Security Layer - JWT Authentication + Protected Routes.
Deliverable 7: Role System (student / mentor / admin).

BEYOND THE ORIGINAL ASK - a real vulnerability fix:
Every endpoint that took a `user_id` path parameter (e.g. GET /dashboard/{user_id},
GET /career-twin/{user_id}) previously had ZERO authorization checks - any
visitor could view or modify ANY user's data just by changing the number in
the URL. This is a textbook IDOR (Insecure Direct Object Reference)
vulnerability, and it's the single most common real-world bug in student
projects. This module fixes it: protected routes now require a valid JWT,
and the token's own user_id must match the requested user_id - a student
cannot view a mentor's dashboard, or another student's resume, by guessing
IDs.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import User

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-insecure-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

if SECRET_KEY == "dev-only-insecure-secret-change-in-production":
    print(
        "[auth] WARNING: using the default JWT secret. Set JWT_SECRET_KEY in "
        "your .env before deploying anywhere real - anyone who knows this "
        "default string can forge valid tokens."
    )


def create_access_token(user_id: int, email: str, role: str) -> str:
    """Issues a signed JWT containing the user's id, email, and role."""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "email": email, "role": role, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decodes and validates a JWT. Raises HTTPException(401) if invalid/expired."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired - please log in again")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")


def _extract_bearer_token(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or malformed Authorization header - expected 'Bearer <token>'",
        )
    return auth_header.removeprefix("Bearer ").strip()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """
    FastAPI dependency - protects a route by requiring a valid JWT. Use as:
        current_user: User = Depends(get_current_user)
    Raises 401 if the token is missing, invalid, expired, or the user no
    longer exists.
    """
    token = _extract_bearer_token(request)
    payload = decode_access_token(token)

    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(status_code=401, detail="User associated with this token no longer exists")
    return user


def verify_same_user_or_admin(request: Request, current_user: User = Depends(get_current_user)) -> User:
    """
    FastAPI dependency - verifies the authenticated user IS the {user_id}
    in the URL path (or is an admin). This is the fix for the IDOR
    vulnerability described above: prevents user A from accessing user B's
    dashboard/career-twin/skills/etc. just by changing the number in the URL.

    Works generically on any route with a {user_id} path parameter - reads
    it directly from the request rather than needing a separate dependency
    written per-route.
    """
    path_user_id = request.path_params.get("user_id")
    if path_user_id is not None and current_user.id != int(path_user_id) and current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this user's data",
        )
    return current_user


def require_role(*allowed_roles: str):
    """
    Returns a dependency that only allows through users with one of the
    given roles. Use as: Depends(require_role("admin"))
    """
    def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"This action requires one of these roles: {', '.join(allowed_roles)}",
            )
        return current_user
    return _check