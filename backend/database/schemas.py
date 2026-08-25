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
    role: str = "student"  # "student" | "mentor" | "admin" - Deliverable 7


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    career_goal: Optional[str] = None
    role: str
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
    role: Optional[str] = None
    access_token: Optional[str] = None
    token_type: str = "bearer"
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


# --------------------------------------------------------------------------
# Phase 11 - Career Twin + Readiness Score + Simulator
# --------------------------------------------------------------------------

class CareerTwinResponse(BaseModel):
    name: str
    target_career: Optional[str]
    current_skills: List[str]
    readiness_score: int
    readiness_breakdown: dict
    resume_score: Optional[int]
    project_count: int
    skill_count: int


class SimulatorRequest(BaseModel):
    user_id: int
    hypothetical_skills: List[str]


class SimulatorStep(BaseModel):
    label: str
    score: int
    skill_added: Optional[str] = None


# --------------------------------------------------------------------------
# Phase 11 - Learning Analytics (weekly report)
# --------------------------------------------------------------------------

class WeeklyReportResponse(BaseModel):
    skills_completed: List[str]
    projects_completed: List[str]
    engagement_days: int
    career_score_delta: Optional[int]


# --------------------------------------------------------------------------
# Phase 11 - Recommendation Feedback Loop
# --------------------------------------------------------------------------

class FeedbackRequest(BaseModel):
    user_id: Optional[int] = None
    recommendation_type: str
    reference: Optional[str] = None
    rating: int
    comment: Optional[str] = None


# --------------------------------------------------------------------------
# Phase 11 - Notification Engine
# --------------------------------------------------------------------------

class NotificationOut(BaseModel):
    id: int
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --------------------------------------------------------------------------
# Phase 11 - Admin Analytics Dashboard
# --------------------------------------------------------------------------

class AdminAnalyticsResponse(BaseModel):
    total_users: int
    active_users_7d: int
    active_users_30d: int
    retention_pct: Optional[float]
    conversion_rate_pct: Optional[float]
    average_resume_score: Optional[float]
    average_feedback_rating: Optional[float]
    top_careers: List[dict]
    top_missing_skills: List[dict]


# --------------------------------------------------------------------------
# Phase 11 - AI Learning Companion
# --------------------------------------------------------------------------

class CompanionChatRequest(BaseModel):
    user_id: int
    question: str


class CompanionChatResponse(BaseModel):
    answer: str


# --------------------------------------------------------------------------
# Phase 11 - Skill Graph
# --------------------------------------------------------------------------

class SkillGraphResponse(BaseModel):
    nodes: List[str]
    edges: List[dict]


# --------------------------------------------------------------------------
# Phase 11 - ML Recommendation Engine v2
# --------------------------------------------------------------------------

class RecommendV2Request(BaseModel):
    skills: List[str]
    interest: Optional[str] = None


class RecommendV2Result(BaseModel):
    career: str
    rule_based_score: float
    ml_score: float
    blended_score: float
    missing_skills: List[str]