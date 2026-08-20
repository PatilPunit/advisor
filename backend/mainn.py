from typing import List, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from recommender import recommend_career
from roadmap import get_roadmap
from project import get_projects_for_career
from resume.parser import extract_text_from_pdf
from resume.extractor import extract_skills
from resume.scorer import calculate_score

from database.db import Base, engine, get_db
from database import crud, schemas

# Creates all tables (users, user_skills, user_projects, resume_history)
# if they don't already exist. Safe to call every startup - it won't
# touch tables that already exist.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Career Advisor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------
# Existing models (Phase 4/6)
# --------------------------------------------------------------------------

class RecommendRequest(BaseModel):
    skills: List[str] = Field(..., example=["Python", "Pandas"])
    interest: Optional[str] = Field(None, example="cybersecurity analyst")


class TopMatch(BaseModel):
    career: str
    score: float


class RecommendResponse(BaseModel):
    career: str
    match_score: float
    missing_skills: List[str]
    required_skills: List[str]
    user_skills: List[str]
    roadmap: List[str]
    projects: List[dict]
    top_matches: List[TopMatch]


class ResumeAnalyzeResponse(BaseModel):
    score: int
    skills: List[str]
    missing: List[str]
    recommended_career: str


# --------------------------------------------------------------------------
# Routes: Phase 4/6 (unchanged)
# --------------------------------------------------------------------------

@app.get("/")
def home():
    return {"message": "AI Career Advisor Running"}


@app.post("/recommend", response_model=RecommendResponse)
def recommend(request: RecommendRequest):
    if not request.skills:
        raise HTTPException(status_code=400, detail="skills list cannot be empty")

    results = recommend_career(request.skills, request.interest, top_n=3)
    if not results:
        raise HTTPException(status_code=404, detail="No matching career found")

    top = results[0]
    roadmap = get_roadmap(top["career"])
    projects = get_projects_for_career(top["beginner_project"], top["advanced_project"])
    top_matches = [
        TopMatch(career=r["career"], score=round(r["match_percent"])) for r in results[:3]
    ]

    return RecommendResponse(
        career=top["career"],
        match_score=top["match_percent"],
        missing_skills=top["missing_skills"],
        required_skills=top["required_skills"],
        user_skills=request.skills,
        roadmap=roadmap,
        projects=projects,
        top_matches=top_matches,
    )


@app.post("/resume-analyze", response_model=ResumeAnalyzeResponse)
async def resume_analyze(
    file: UploadFile = File(...),
    user_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a .pdf file")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        resume_text = extract_text_from_pdf(file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not resume_text.strip():
        raise HTTPException(
            status_code=422,
            detail="No readable text found in this PDF (it may be a scanned image).",
        )

    detected_skills = extract_skills(resume_text)
    if not detected_skills:
        raise HTTPException(status_code=422, detail="No recognizable skills found in this resume.")

    top_career_result = recommend_career(detected_skills, interest=None, top_n=1)[0]
    recommended_career = top_career_result["career"]
    required_skills = top_career_result["required_skills"]

    score_result = calculate_score(detected_skills, required_skills)

    # STEP 12: if the request came from a logged-in user, save this score
    # to their resume_history so they can see improvement over time.
    if user_id is not None:
        user = crud.get_user(db, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail=f"No user with id {user_id}")
        crud.add_resume_score(db, user_id, score_result["score"])

    return ResumeAnalyzeResponse(
        score=score_result["score"],
        skills=detected_skills,
        missing=score_result["missing"],
        recommended_career=recommended_career,
    )


# --------------------------------------------------------------------------
# Routes: Phase 8 - Auth
# --------------------------------------------------------------------------

@app.post("/register", response_model=schemas.UserOut)
def register(request: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, request.email):
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    user = crud.create_user(db, request.name, request.email, request.password)
    return user


@app.post("/login", response_model=schemas.LoginResponse)
def login(request: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, request.email, request.password)
    if not user:
        return schemas.LoginResponse(success=False, message="Invalid email or password")

    return schemas.LoginResponse(success=True, user_id=user.id, name=user.name)


# --------------------------------------------------------------------------
# Routes: Phase 8 - Career goal, skills, projects
# --------------------------------------------------------------------------

@app.post("/users/{user_id}/goal", response_model=schemas.UserOut)
def set_goal(user_id: int, request: schemas.SetGoalRequest, db: Session = Depends(get_db)):
    try:
        user = crud.set_career_goal(db, user_id, request.career)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return user


@app.get("/users/{user_id}/skills", response_model=List[schemas.SkillOut])
def list_skills(user_id: int, db: Session = Depends(get_db)):
    return crud.get_user_skills(db, user_id)


@app.post("/users/{user_id}/skills", response_model=schemas.SkillOut)
def update_skill(user_id: int, request: schemas.SkillUpdateRequest, db: Session = Depends(get_db)):
    return crud.update_skill_completion(db, user_id, request.skill_name, request.completed)


@app.get("/users/{user_id}/projects", response_model=List[schemas.ProjectOut])
def list_projects(user_id: int, db: Session = Depends(get_db)):
    return crud.get_user_projects(db, user_id)


@app.post("/users/{user_id}/projects", response_model=schemas.ProjectOut)
def update_project(user_id: int, request: schemas.ProjectUpdateRequest, db: Session = Depends(get_db)):
    return crud.update_project_completion(db, user_id, request.project_name, request.completed)


# --------------------------------------------------------------------------
# Routes: Phase 8 - STEP 13 Dashboard
# --------------------------------------------------------------------------

@app.get("/dashboard/{user_id}", response_model=schemas.DashboardResponse)
def dashboard(user_id: int, db: Session = Depends(get_db)):
    try:
        data = crud.get_dashboard_data(db, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return data