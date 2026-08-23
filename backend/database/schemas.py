"""
database/schemas.py
----------------------
Pydantic models for request/response validation - separate from models.py
(which defines actual DB tables). This is the standard FastAPI pattern:
models.py = database shape, schemas.py = API input/output shape.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


# --------------------------------------------------------------------------
# STEP 7 - Registration
# --------------------------------------------------------------------------

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    career_goal: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --------------------------------------------------------------------------
# STEP 8 - Login
# --------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    success: bool
    user_id: Optional[int] = None
    name: Optional[str] = None
    message: Optional[str] = None


# --------------------------------------------------------------------------
# Career goal
# --------------------------------------------------------------------------

class SetGoalRequest(BaseModel):
    career: str


# --------------------------------------------------------------------------
# STEP 9/10 - Skill completion
# --------------------------------------------------------------------------

class SkillUpdateRequest(BaseModel):
    skill_name: str
    completed: bool = True


class SkillOut(BaseModel):
    skill_name: str
    completed: bool

    class Config:
        from_attributes = True


# --------------------------------------------------------------------------
# Project completion
# --------------------------------------------------------------------------

class ProjectUpdateRequest(BaseModel):
    project_name: str
    completed: bool = True


class ProjectOut(BaseModel):
    project_name: str
    completed: bool

    class Config:
        from_attributes = True


# --------------------------------------------------------------------------
# STEP 12 - Resume history
# --------------------------------------------------------------------------

class ResumeHistoryOut(BaseModel):
    score: int
    upload_date: datetime

    class Config:
        from_attributes = True


# --------------------------------------------------------------------------
# STEP 13 - Dashboard
# --------------------------------------------------------------------------

class DashboardResponse(BaseModel):
    name: str
    career_goal: Optional[str]
    career_match: float
    resume_score: Optional[int]
    completed_skills: int
    total_skills: int
    completed_projects: int
    total_projects: int
    roadmap_progress: float
    resume_history: List[ResumeHistoryOut]


# --------------------------------------------------------------------------
# Phase 10 - AI Mentor
# --------------------------------------------------------------------------

class MentorChatRequest(BaseModel):
    question: str
    user_id: Optional[int] = None


class MentorChatResponse(BaseModel):
    answer: str
    recommended_career: Optional[str] = None
    possessed_skills: List[str] = []
    missing_skills: List[str] = []
    suggested_project: Optional[str] = None


# --------------------------------------------------------------------------
# Phase 10 - Dynamic Roadmap
# --------------------------------------------------------------------------

class DynamicRoadmapRequest(BaseModel):
    career: str
    known_skills: List[str]


# --------------------------------------------------------------------------
# Phase 10 - Career Probability Engine
# --------------------------------------------------------------------------

class CareerProbability(BaseModel):
    career: str
    probability: float


class CareerProbabilityRequest(BaseModel):
    skills: List[str]
    user_id: Optional[int] = None


# --------------------------------------------------------------------------
# Phase 10 - Job Matching
# --------------------------------------------------------------------------

class JobMatchResponse(BaseModel):
    match_score: int
    missing_keywords: List[str]
    recommended_actions: List[str]
    note: Optional[str] = None


# --------------------------------------------------------------------------
# Phase 10 - Project Generator
# --------------------------------------------------------------------------

class ProjectGeneratorRequest(BaseModel):
    domain: str
    level: str
    user_id: Optional[int] = None


class ProjectGeneratorResponse(BaseModel):
    project_name: str
    domain: str
    difficulty: str
    dataset: str
    skills: List[str]
    timeline: str


# --------------------------------------------------------------------------
# Phase 10 - Learning Time Predictor
# --------------------------------------------------------------------------

class LearningTimeRequest(BaseModel):
    career: str
    current_skills: List[str]


class LearningTimeResponse(BaseModel):
    estimated_duration: str
    weekly_hours: int
    difficulty: str
    remaining_skills: List[str]


# --------------------------------------------------------------------------
# Phase 10 - Analytics Dashboard
# --------------------------------------------------------------------------

class AnalyticsSummaryResponse(BaseModel):
    most_chosen_career: Optional[str]
    most_missing_skill: Optional[str]
    average_resume_score: Optional[float]
    daily_active_users: int