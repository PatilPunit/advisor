"""
database/crud.py
-------------------
All actual database operations (Create, Read, Update, Delete) live here.
Routes in main.py call these functions instead of touching the DB directly -
keeps main.py focused on HTTP concerns, crud.py focused on data.
"""

from __future__ import annotations

from typing import List, Optional

import bcrypt
from sqlalchemy.orm import Session

from database.models import ResumeHistory, User, UserProject, UserSkill
from roadmap import get_roadmap
from recommender import recommend_career


# --------------------------------------------------------------------------
# Password hashing (bcrypt directly - simpler and more reliable than
# passlib, which has a known compatibility issue with newer bcrypt versions)
# --------------------------------------------------------------------------

def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


# --------------------------------------------------------------------------
# STEP 7 - Registration
# --------------------------------------------------------------------------

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, name: str, email: str, password: str) -> User:
    user = User(
        name=name,
        email=email,
        hashed_password=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# --------------------------------------------------------------------------
# STEP 8 - Login
# --------------------------------------------------------------------------

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# --------------------------------------------------------------------------
# Career goal + seeding roadmap/projects
# --------------------------------------------------------------------------

def set_career_goal(db: Session, user_id: int, career: str) -> User:
    """
    Sets the user's career goal and seeds their roadmap skills + projects
    (if not already seeded) so progress can be tracked against real data
    from skill_roadmap.csv and career_paths.csv.
    """
    user = get_user(db, user_id)
    if not user:
        raise ValueError(f"No user with id {user_id}")

    user.career_goal = career

    # Seed roadmap skills, only for skills not already tracked for this user
    existing_skill_names = {
        s.skill_name.lower() for s in db.query(UserSkill).filter(UserSkill.user_id == user_id)
    }
    for skill in get_roadmap(career):
        if skill.lower() not in existing_skill_names:
            db.add(UserSkill(user_id=user_id, skill_name=skill, completed=False))

    db.commit()
    db.refresh(user)
    return user


# --------------------------------------------------------------------------
# STEP 9/10 - Skill completion
# --------------------------------------------------------------------------

def get_user_skills(db: Session, user_id: int) -> List[UserSkill]:
    return db.query(UserSkill).filter(UserSkill.user_id == user_id).all()


def update_skill_completion(
    db: Session, user_id: int, skill_name: str, completed: bool
) -> UserSkill:
    row = (
        db.query(UserSkill)
        .filter(UserSkill.user_id == user_id, UserSkill.skill_name.ilike(skill_name))
        .first()
    )
    if row is None:
        # skill not seeded yet (e.g. user hasn't set a career goal) - create it
        row = UserSkill(user_id=user_id, skill_name=skill_name, completed=completed)
        db.add(row)
    else:
        row.completed = completed

    db.commit()
    db.refresh(row)
    return row


# --------------------------------------------------------------------------
# Project completion
# --------------------------------------------------------------------------

def get_user_projects(db: Session, user_id: int) -> List[UserProject]:
    return db.query(UserProject).filter(UserProject.user_id == user_id).all()


def update_project_completion(
    db: Session, user_id: int, project_name: str, completed: bool
) -> UserProject:
    row = (
        db.query(UserProject)
        .filter(UserProject.user_id == user_id, UserProject.project_name.ilike(project_name))
        .first()
    )
    if row is None:
        row = UserProject(user_id=user_id, project_name=project_name, completed=completed)
        db.add(row)
    else:
        row.completed = completed

    db.commit()
    db.refresh(row)
    return row


# --------------------------------------------------------------------------
# STEP 12 - Resume history
# --------------------------------------------------------------------------

def add_resume_score(db: Session, user_id: int, score: int) -> ResumeHistory:
    row = ResumeHistory(user_id=user_id, score=score)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_resume_history(db: Session, user_id: int) -> List[ResumeHistory]:
    return (
        db.query(ResumeHistory)
        .filter(ResumeHistory.user_id == user_id)
        .order_by(ResumeHistory.upload_date.asc())
        .all()
    )


# --------------------------------------------------------------------------
# STEP 11/13 - Progress calculator + dashboard
# --------------------------------------------------------------------------

def get_dashboard_data(db: Session, user_id: int) -> dict:
    user = get_user(db, user_id)
    if not user:
        raise ValueError(f"No user with id {user_id}")

    # --- Roadmap progress: completed / total * 100 ---
    skills = get_user_skills(db, user_id)
    total_skills = len(skills)
    completed_skills = sum(1 for s in skills if s.completed)
    roadmap_progress = (
        round((completed_skills / total_skills) * 100) if total_skills else 0
    )

    # --- Projects progress ---
    projects = get_user_projects(db, user_id)
    total_projects = len(projects)
    completed_projects = sum(1 for p in projects if p.completed)

    # --- Career match: reuse the existing recommender, scored against the
    #     user's own completed skills, so it stays in sync with Phase 4/8 logic ---
    completed_skill_names = [s.skill_name for s in skills if s.completed]
    career_match = 0.0
    if user.career_goal and completed_skill_names:
        all_results = recommend_career(completed_skill_names, user.career_goal, top_n=8)
        match = next(
            (r for r in all_results if r["career"].lower() == user.career_goal.lower()),
            None,
        )
        if match:
            career_match = match["match_percent"]

    # --- Resume score: most recent upload ---
    history = get_resume_history(db, user_id)
    latest_resume_score = history[-1].score if history else None

    return {
        "name": user.name,
        "career_goal": user.career_goal,
        "career_match": career_match,
        "resume_score": latest_resume_score,
        "completed_skills": completed_skills,
        "total_skills": total_skills,
        "completed_projects": completed_projects,
        "total_projects": total_projects,
        "roadmap_progress": roadmap_progress,
        "resume_history": history,
    }