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