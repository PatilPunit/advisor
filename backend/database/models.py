"""
database/models.py
---------------------
SQLAlchemy ORM models - the actual database tables.

Tables:
  - User            : account info + chosen career goal
  - UserSkill       : one row per roadmap skill per user, with completed flag
  - UserProject     : one row per recommended project per user, with completed flag
  - ResumeHistory   : one row per resume upload, so score improvement over time is visible
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from database.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    career_goal = Column(String, nullable=True)  # e.g. "ML Engineer"
    role = Column(String, nullable=False, default="student", index=True)  # "student" | "mentor" | "admin"
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    skills = relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("UserProject", back_populates="user", cascade="all, delete-orphan")
    resume_history = relationship("ResumeHistory", back_populates="user", cascade="all, delete-orphan")


class UserSkill(Base):
    __tablename__ = "user_skills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_name = Column(String, nullable=False)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)  # Phase 11: needed for weekly reports + staleness checks

    user = relationship("User", back_populates="skills")


class UserProject(Base):
    __tablename__ = "user_projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_name = Column(String, nullable=False)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="projects")


class ResumeHistory(Base):
    __tablename__ = "resume_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Integer, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="resume_history")


# --------------------------------------------------------------------------
# Phase 10 - Analytics + AI feature history tables
# --------------------------------------------------------------------------

class MentorChat(Base):
    """One row per question asked to the AI Mentor - the conversation memory."""
    __tablename__ = "mentor_chats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # nullable: guests can chat too
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    recommended_career = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserActivity(Base):
    """One row per meaningful action - powers the Analytics Dashboard."""
    __tablename__ = "user_activity"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action_type = Column(String, nullable=False)  # e.g. "recommend", "resume_analyze", "mentor_chat"
    created_at = Column(DateTime, default=datetime.utcnow)


class CareerRecommendation(Base):
    """One row per /recommend call - powers 'Most Chosen Career' + 'Most Missing Skill'."""
    __tablename__ = "career_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    career = Column(String, nullable=False)
    match_percent = Column(Integer, nullable=False)
    missing_skills = Column(String, nullable=True)  # comma-joined for simple storage
    created_at = Column(DateTime, default=datetime.utcnow)


class JobMatch(Base):
    """One row per resume-vs-job-description match performed."""
    __tablename__ = "job_matches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    match_score = Column(Integer, nullable=False)
    missing_keywords = Column(String, nullable=True)  # comma-joined
    created_at = Column(DateTime, default=datetime.utcnow)


class CareerPrediction(Base):
    """One row per career-probability calculation (Deliverable 5)."""
    __tablename__ = "career_predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    career = Column(String, nullable=False)
    probability = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ProjectRecommendation(Base):
    """One row per AI-generated project suggestion (Deliverable 6)."""
    __tablename__ = "project_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    project_name = Column(String, nullable=True)
    domain = Column(String, nullable=True)
    difficulty = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# --------------------------------------------------------------------------
# Phase 11 - Platform Intelligence & Ecosystem
# --------------------------------------------------------------------------

class CareerProfile(Base):
    """
    Deliverable 1: Career Twin. One row per user - their persistent 'Career
    DNA'. Recomputed and upserted every time the readiness score is
    calculated (dashboard visit, skill/project toggle, resume upload).
    """
    __tablename__ = "career_profile"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    target_career = Column(String, nullable=True)
    current_score = Column(Integer, default=0)      # readiness score, 0-100
    readiness_score = Column(Integer, default=0)     # kept as a distinct field per spec; mirrors current_score today
    skill_count = Column(Integer, default=0)
    project_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CareerScoreSnapshot(Base):
    """
    Historical readiness-score snapshots - powers weekly report deltas
    ("Career Score: +8") and trend charts. Without storing history, "how
    much did I improve this week" is structurally impossible to answer.
    """
    __tablename__ = "career_score_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Integer, nullable=False)
    snapshot_date = Column(DateTime, default=datetime.utcnow)


class RecommendationFeedback(Base):
    """Deliverable 5: user ratings on recommendations (roadmap, project, mentor answer, etc.)."""
    __tablename__ = "recommendation_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    recommendation_type = Column(String, nullable=False)  # e.g. "roadmap", "project", "mentor_answer"
    reference = Column(String, nullable=True)  # e.g. the career/project name being rated
    rating = Column(Integer, nullable=False)   # 1-5 stars
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    """Deliverable 7: in-app notifications (staleness nudges, milestones, etc.)."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)