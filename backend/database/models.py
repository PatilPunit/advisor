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
    created_at = Column(DateTime, default=datetime.utcnow)

    skills = relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("UserProject", back_populates="user", cascade="all, delete-orphan")
    resume_history = relationship("ResumeHistory", back_populates="user", cascade="all, delete-orphan")


class UserSkill(Base):
    __tablename__ = "user_skills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_name = Column(String, nullable=False)
    completed = Column(Boolean, default=False)

    user = relationship("User", back_populates="skills")


class UserProject(Base):
    __tablename__ = "user_projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_name = Column(String, nullable=False)
    completed = Column(Boolean, default=False)

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
    project_name = Column(String, nullable=False)
    domain = Column(String, nullable=True)
    difficulty = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)