"""
database/crud.py
-------------------
All actual database operations (Create, Read, Update, Delete) live here.
Routes in main.py call these functions instead of touching the DB directly -
keeps main.py focused on HTTP concerns, crud.py focused on data.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

import bcrypt
from sqlalchemy.orm import Session

from database.models import (
    CareerProfile, CareerRecommendation, CareerScoreSnapshot, JobMatch,
    MentorChat, Notification, ProjectRecommendation, RecommendationFeedback,
    ResumeHistory, User, UserActivity, UserProject, UserSkill,
)
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


VALID_ROLES = {"student", "mentor", "admin"}


def create_user(db: Session, name: str, email: str, password: str, role: str = "student") -> User:
    if role not in VALID_ROLES:
        role = "student"  # never let an invalid/unexpected role silently grant elevated access

    user = User(
        name=name,
        email=email,
        hashed_password=hash_password(password),
        role=role,
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
    Sets the user's career goal and syncs BOTH their roadmap skills AND
    tracked projects to match it.

    If the user previously had a different career goal, skills/projects
    that belong ONLY to the old career are removed (so switching goals
    doesn't leave a mixed, ambiguous checklist combining two different
    careers). Items shared between old and new (e.g. "Python" appears in
    almost every roadmap) keep their completed status - only truly
    unrelated old items are dropped.
    """
    from recommender import _load_career_data

    user = get_user(db, user_id)
    if not user:
        raise ValueError(f"No user with id {user_id}")

    user.career_goal = career

    # --- Skills ---
    new_roadmap = get_roadmap(career)
    new_roadmap_lower = {s.lower() for s in new_roadmap}

    existing_skill_rows = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    existing_skills_by_name = {row.skill_name.lower(): row for row in existing_skill_rows}

    for name_lower, row in existing_skills_by_name.items():
        if name_lower not in new_roadmap_lower:
            db.delete(row)

    for skill in new_roadmap:
        if skill.lower() not in existing_skills_by_name:
            db.add(UserSkill(user_id=user_id, skill_name=skill, completed=False))

    # --- Projects (beginner + advanced, from career_paths.csv) ---
    career_data = next(
        (c for c in _load_career_data() if c["career"].lower() == career.lower()), None
    )
    new_project_names_lower = set()
    if career_data:
        new_project_names_lower = {
            career_data["beginner_projects"].lower(), career_data["advanced_projects"].lower()
        }

    existing_project_rows = db.query(UserProject).filter(UserProject.user_id == user_id).all()
    existing_projects_by_name = {row.project_name.lower(): row for row in existing_project_rows}

    for name_lower, row in existing_projects_by_name.items():
        if name_lower not in new_project_names_lower:
            db.delete(row)

    if career_data:
        for project_name in [career_data["beginner_projects"], career_data["advanced_projects"]]:
            if project_name and project_name.lower() not in existing_projects_by_name:
                db.add(UserProject(user_id=user_id, project_name=project_name, completed=False))

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
    now = datetime.utcnow()
    if row is None:
        # skill not seeded yet (e.g. user hasn't set a career goal) - create it
        row = UserSkill(
            user_id=user_id, skill_name=skill_name, completed=completed,
            completed_at=now if completed else None,
        )
        db.add(row)
    else:
        row.completed = completed
        row.completed_at = now if completed else None

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
    now = datetime.utcnow()
    if row is None:
        row = UserProject(
            user_id=user_id, project_name=project_name, completed=completed,
            completed_at=now if completed else None,
        )
        db.add(row)
    else:
        row.completed = completed
        row.completed_at = now if completed else None

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


# --------------------------------------------------------------------------
# Phase 10 - Activity logging + AI feature history
# --------------------------------------------------------------------------

def log_activity(db: Session, user_id: Optional[int], action_type: str) -> None:
    db.add(UserActivity(user_id=user_id, action_type=action_type))
    db.commit()


def log_mentor_chat(
    db: Session, user_id: Optional[int], question: str, answer: str,
    recommended_career: Optional[str],
) -> MentorChat:
    row = MentorChat(
        user_id=user_id, question=question, answer=answer,
        recommended_career=recommended_career,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    log_activity(db, user_id, "mentor_chat")
    return row


def get_mentor_history(db: Session, user_id: int) -> List[MentorChat]:
    """Conversation memory: past questions/answers for a logged-in user."""
    return (
        db.query(MentorChat)
        .filter(MentorChat.user_id == user_id)
        .order_by(MentorChat.created_at.asc())
        .all()
    )


def log_career_recommendation(
    db: Session, user_id: Optional[int], career: str, match_percent: float,
    missing_skills: List[str],
) -> None:
    db.add(CareerRecommendation(
        user_id=user_id,
        career=career,
        match_percent=round(match_percent),
        missing_skills=",".join(missing_skills),
    ))
    db.commit()
    log_activity(db, user_id, "recommend")


def log_job_match(
    db: Session, user_id: Optional[int], match_score: int, missing_keywords: List[str],
) -> None:
    db.add(JobMatch(
        user_id=user_id,
        match_score=match_score,
        missing_keywords=",".join(missing_keywords),
    ))
    db.commit()
    log_activity(db, user_id, "job_match")


def log_project_recommendation(
    db: Session, user_id: Optional[int], project_name: str, domain: str, difficulty: str,
) -> None:
    db.add(ProjectRecommendation(
        user_id=user_id, project_name=project_name, domain=domain, difficulty=difficulty,
    ))
    db.commit()
    log_activity(db, user_id, "project_generator")


def log_resume_analyze_activity(db: Session, user_id: Optional[int]) -> None:
    log_activity(db, user_id, "resume_analyze")


# --------------------------------------------------------------------------
# Phase 10 - Analytics Dashboard aggregation
# --------------------------------------------------------------------------

def get_analytics_summary(db: Session) -> dict:
    from collections import Counter
    from datetime import datetime, timedelta

    # Most chosen career: mode of career_recommendations.career
    all_recs = db.query(CareerRecommendation).all()
    career_counts = Counter(r.career for r in all_recs)
    most_chosen_career = career_counts.most_common(1)[0][0] if career_counts else None

    # Most missing skill: flatten every comma-joined missing_skills field, take the mode
    skill_counts = Counter()
    for r in all_recs:
        if r.missing_skills:
            skill_counts.update(s.strip() for s in r.missing_skills.split(",") if s.strip())
    most_missing_skill = skill_counts.most_common(1)[0][0] if skill_counts else None

    # Average resume score across all resume_history rows
    all_scores = [r.score for r in db.query(ResumeHistory).all()]
    average_resume_score = round(sum(all_scores) / len(all_scores), 1) if all_scores else None

    # Daily active users: distinct user_ids with activity in the last 24h
    since = datetime.utcnow() - timedelta(days=1)
    recent_activity = (
        db.query(UserActivity)
        .filter(UserActivity.created_at >= since, UserActivity.user_id.isnot(None))
        .all()
    )
    daily_active_users = len({a.user_id for a in recent_activity})

    return {
        "most_chosen_career": most_chosen_career,
        "most_missing_skill": most_missing_skill,
        "average_resume_score": average_resume_score,
        "daily_active_users": daily_active_users,
    }


# --------------------------------------------------------------------------
# Phase 11 - Career Twin (Deliverable 1) + score history
# --------------------------------------------------------------------------

def upsert_career_profile(
    db: Session, user_id: int, target_career: Optional[str], readiness_score: int,
    skill_count: int, project_count: int,
) -> CareerProfile:
    profile = db.query(CareerProfile).filter(CareerProfile.user_id == user_id).first()
    if profile is None:
        profile = CareerProfile(user_id=user_id)
        db.add(profile)

    profile.target_career = target_career
    profile.current_score = readiness_score
    profile.readiness_score = readiness_score
    profile.skill_count = skill_count
    profile.project_count = project_count

    db.commit()
    db.refresh(profile)
    return profile


def add_score_snapshot(db: Session, user_id: int, score: int) -> None:
    db.add(CareerScoreSnapshot(user_id=user_id, score=score))
    db.commit()


def add_score_snapshot_if_new_day(db: Session, user_id: int, score: int) -> None:
    """Avoids flooding the history table with a snapshot every single page load."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    existing_today = (
        db.query(CareerScoreSnapshot)
        .filter(CareerScoreSnapshot.user_id == user_id, CareerScoreSnapshot.snapshot_date >= today_start)
        .first()
    )
    if not existing_today:
        add_score_snapshot(db, user_id, score)


def get_score_snapshots(db: Session, user_id: int, days: int = 30) -> List[CareerScoreSnapshot]:
    since = datetime.utcnow() - timedelta(days=days)
    return (
        db.query(CareerScoreSnapshot)
        .filter(CareerScoreSnapshot.user_id == user_id, CareerScoreSnapshot.snapshot_date >= since)
        .order_by(CareerScoreSnapshot.snapshot_date.asc())
        .all()
    )


def get_latest_job_match_score(db: Session, user_id: int) -> Optional[int]:
    row = (
        db.query(JobMatch)
        .filter(JobMatch.user_id == user_id)
        .order_by(JobMatch.created_at.desc())
        .first()
    )
    return row.match_score if row else None


# --------------------------------------------------------------------------
# Phase 11 - Learning Analytics Engine (Deliverable 4)
# --------------------------------------------------------------------------

def get_weekly_report(db: Session, user_id: int) -> dict:
    since = datetime.utcnow() - timedelta(days=7)

    skills_completed_this_week = (
        db.query(UserSkill)
        .filter(UserSkill.user_id == user_id, UserSkill.completed == True,  # noqa: E712
                UserSkill.completed_at >= since)
        .all()
    )
    projects_completed_this_week = (
        db.query(UserProject)
        .filter(UserProject.user_id == user_id, UserProject.completed == True,  # noqa: E712
                UserProject.completed_at >= since)
        .all()
    )

    # "Engagement days" - a defensible, honestly-measurable proxy for "time
    # spent" (we don't instrument actual session duration anywhere, so we
    # don't fabricate an hours/minutes figure - we report distinct days
    # with any logged activity in the last week instead).
    recent_activity = (
        db.query(UserActivity)
        .filter(UserActivity.user_id == user_id, UserActivity.created_at >= since)
        .all()
    )
    engagement_days = len({a.created_at.date() for a in recent_activity})

    # Career score delta vs a week ago
    snapshots = get_score_snapshots(db, user_id, days=8)
    score_delta = None
    if len(snapshots) >= 2:
        score_delta = snapshots[-1].score - snapshots[0].score

    return {
        "skills_completed": [s.skill_name for s in skills_completed_this_week],
        "projects_completed": [p.project_name for p in projects_completed_this_week],
        "engagement_days": engagement_days,
        "career_score_delta": score_delta,
    }


# --------------------------------------------------------------------------
# Phase 11 - Recommendation Feedback Loop (Deliverable 5)
# --------------------------------------------------------------------------

def add_feedback(
    db: Session, user_id: Optional[int], recommendation_type: str,
    reference: Optional[str], rating: int, comment: Optional[str],
) -> RecommendationFeedback:
    row = RecommendationFeedback(
        user_id=user_id, recommendation_type=recommendation_type,
        reference=reference, rating=rating, comment=comment,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_average_feedback_rating(db: Session) -> Optional[float]:
    ratings = [r.rating for r in db.query(RecommendationFeedback).all()]
    return round(sum(ratings) / len(ratings), 2) if ratings else None


# --------------------------------------------------------------------------
# Phase 11 - Notification Engine (Deliverable 7)
# --------------------------------------------------------------------------

def generate_notifications_if_needed(db: Session, user_id: int) -> None:
    """
    Checks whether the user has gone stale (no skill completed in 7+ days)
    and creates a fresh notification if so - but never spams duplicates,
    only creates one if the most recent notification is older than 3 days.
    Called lazily whenever /notifications/{user_id} is hit (no background
    scheduler in this stack, so staleness is checked on-demand instead).
    """
    skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    completed_dates = [s.completed_at for s in skills if s.completed and s.completed_at]
    last_activity = max(completed_dates) if completed_dates else None

    is_stale = last_activity is None or (datetime.utcnow() - last_activity).days >= 7
    if not is_stale:
        return

    recent_notif = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .first()
    )
    if recent_notif and (datetime.utcnow() - recent_notif.created_at).days < 3:
        return  # already nudged recently, don't spam

    next_skill = next((s.skill_name for s in skills if not s.completed), None)
    days_str = f"{(datetime.utcnow() - last_activity).days} days" if last_activity else "a while"
    message = f"You haven't updated your roadmap in {days_str}."
    if next_skill:
        message += f" Recommended: Complete {next_skill}."

    db.add(Notification(user_id=user_id, message=message))
    db.commit()


def get_notifications(db: Session, user_id: int, unread_only: bool = False) -> List[Notification]:
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if unread_only:
        query = query.filter(Notification.is_read == False)  # noqa: E712
    return query.order_by(Notification.created_at.desc()).all()


def mark_notification_read(db: Session, notification_id: int) -> None:
    row = db.query(Notification).filter(Notification.id == notification_id).first()
    if row:
        row.is_read = True
        db.commit()


# --------------------------------------------------------------------------
# Phase 11 - Admin Analytics Dashboard (Deliverable 6) - expanded
# --------------------------------------------------------------------------

def get_admin_analytics(db: Session) -> dict:
    total_users = db.query(User).count()

    since_7d = datetime.utcnow() - timedelta(days=7)
    since_14d = datetime.utcnow() - timedelta(days=14)
    since_30d = datetime.utcnow() - timedelta(days=30)

    active_last_7d = {
        a.user_id for a in db.query(UserActivity)
        .filter(UserActivity.created_at >= since_7d, UserActivity.user_id.isnot(None)).all()
    }
    active_prior_7d = {
        a.user_id for a in db.query(UserActivity)
        .filter(UserActivity.created_at >= since_14d, UserActivity.created_at < since_7d,
                UserActivity.user_id.isnot(None)).all()
    }
    active_last_30d = {
        a.user_id for a in db.query(UserActivity)
        .filter(UserActivity.created_at >= since_30d, UserActivity.user_id.isnot(None)).all()
    }

    # Simple retention proxy: of users active in the PRIOR week, what % came back this week
    retention_pct = None
    if active_prior_7d:
        retained = active_prior_7d & active_last_7d
        retention_pct = round((len(retained) / len(active_prior_7d)) * 100, 1)

    # Deliverable 11: SaaS Analytics - Conversion Rate.
    # "Conversion" here means: of everyone who registered, what % actually
    # set a career goal (i.e. engaged past signup into real product use) -
    # a defensible, honestly-measurable proxy since this product has no
    # separate "paid" tier yet to convert into.
    users_with_goal = db.query(User).filter(User.career_goal.isnot(None)).count()
    conversion_rate_pct = round((users_with_goal / total_users) * 100, 1) if total_users else None

    base_summary = get_analytics_summary(db)

    from collections import Counter
    all_recs = db.query(CareerRecommendation).all()
    career_counts = Counter(r.career for r in all_recs)
    top_careers = career_counts.most_common(5)

    skill_counts = Counter()
    for r in all_recs:
        if r.missing_skills:
            skill_counts.update(s.strip() for s in r.missing_skills.split(",") if s.strip())
    top_missing_skills = skill_counts.most_common(5)

    return {
        "total_users": total_users,
        "active_users_7d": len(active_last_7d),
        "active_users_30d": len(active_last_30d),
        "retention_pct": retention_pct,
        "conversion_rate_pct": conversion_rate_pct,
        "average_resume_score": base_summary["average_resume_score"],
        "average_feedback_rating": get_average_feedback_rating(db),
        "top_careers": [{"career": c, "count": n} for c, n in top_careers],
        "top_missing_skills": [{"skill": s, "count": n} for s, n in top_missing_skills],
    }