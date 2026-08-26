from typing import List, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from recommender import recommend_career
from roadmap1 import get_roadmap, generate_dynamic_roadmap
from project import get_projects_for_career
from resume.parser import extract_text_from_pdf
from resume.extractor import extract_skills
from resume.scorer import calculate_score
from resume.intelligence import evaluate_resume

from ai_mentor import answer_career_question, answer_companion_question
from job_match import extract_job_skills, match_resume_to_job
from project_generator import generate_project
from learning_time import estimate_learning_time
from career_twin import compute_readiness_score, simulate_learning_path
from skill_graph import generate_skill_graph
from recommender_ml import recommend_career_v2

from database.db import Base, engine, get_db
from database import crud, sc
from auth import create_access_token, get_current_user, verify_same_user_or_admin, require_role
from logging_config import logger, log_user_login, log_resume_upload, log_roadmap_generation, log_job_match, log_error
from file_storage import save_resume_file

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Career Advisor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Deliverable 4: Monitoring - exposes GET /metrics in Prometheus's scrape
# format, tracking request count, error rate (by status code), and
# response time percentiles automatically for every endpoint - no manual
# instrumentation needed per-route.
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


# --------------------------------------------------------------------------
# Existing models (Phase 4/6)
# --------------------------------------------------------------------------

class RecommendRequest(BaseModel):
    skills: List[str] = Field(..., example=["Python", "Pandas"])
    interest: Optional[str] = Field(None, example="cybersecurity analyst")
    user_id: Optional[int] = None


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
    intelligence_score: int
    weaknesses: List[str]
    structural_strengths: List[str]


# --------------------------------------------------------------------------
# Routes: Phase 4/6
# --------------------------------------------------------------------------

@app.get("/")
def home():
    return {"message": "AI Career Advisor Running"}


@app.post("/recommend", response_model=RecommendResponse)
def recommend(request: RecommendRequest, db: Session = Depends(get_db)):
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

    # Phase 10: log this recommendation for analytics (Most Chosen Career / Most Missing Skill)
    crud.log_career_recommendation(
        db, request.user_id, top["career"], top["match_percent"], top["missing_skills"]
    )

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

    # Phase 10: Resume Intelligence Engine - structural evaluation
    intelligence = evaluate_resume(resume_text, score_result["score"])

    if user_id is not None:
        user = crud.get_user(db, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail=f"No user with id {user_id}")
        crud.add_resume_score(db, user_id, intelligence["score"])
        save_resume_file(user_id, file.filename, file_bytes)  # Deliverable 9: versioned storage
        log_resume_upload(user_id, file.filename, intelligence["score"])  # Deliverable 5
    crud.log_resume_analyze_activity(db, user_id)

    return ResumeAnalyzeResponse(
        score=score_result["score"],
        skills=detected_skills,
        missing=score_result["missing"],
        recommended_career=recommended_career,
        intelligence_score=intelligence["score"],
        weaknesses=intelligence["weaknesses"],
        structural_strengths=intelligence["structural_strengths"],
    )


# --------------------------------------------------------------------------
# Routes: Auth
# --------------------------------------------------------------------------

@app.post("/register", response_model=schemas.UserOut)
def register(request: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, request.email):
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    # SECURITY: public registration can never grant "admin" - that would be
    # a privilege-escalation hole (anyone could just POST role="admin").
    # Admin accounts must be created directly in the database or promoted
    # by an existing admin via a separate authenticated action.
    safe_role = request.role if request.role in ("student", "mentor") else "student"

    user = crud.create_user(db, request.name, request.email, request.password, safe_role)
    return user


@app.post("/login", response_model=schemas.LoginResponse)
def login(request: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, request.email, request.password)
    if not user:
        log_user_login(request.email, success=False)
        return schemas.LoginResponse(success=False, message="Invalid email or password")

    log_user_login(request.email, success=True)
    token = create_access_token(user.id, user.email, user.role)
    return schemas.LoginResponse(
        success=True, user_id=user.id, name=user.name, role=user.role, access_token=token,
    )


# --------------------------------------------------------------------------
# Routes: Career goal, skills, projects
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


@app.get("/dashboard/{user_id}", response_model=schemas.DashboardResponse)
def dashboard(user_id: int, db: Session = Depends(get_db), current_user=Depends(verify_same_user_or_admin)):
    try:
        data = crud.get_dashboard_data(db, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return data


# --------------------------------------------------------------------------
# Phase 10 - Deliverable 1: AI Mentor
# --------------------------------------------------------------------------

@app.post("/mentor/chat", response_model=schemas.MentorChatResponse)
def mentor_chat(request: schemas.MentorChatRequest, db: Session = Depends(get_db)):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="question cannot be empty")

    # If logged in, factor in their already-completed roadmap skills too
    user_skills: List[str] = []
    conversation_history = None
    if request.user_id is not None:
        skills = crud.get_user_skills(db, request.user_id)
        user_skills = [s.skill_name for s in skills if s.completed]

        past_chats = crud.get_mentor_history(db, request.user_id)
        if past_chats:
            conversation_history = [
                {"question": c.question, "answer": c.answer} for c in past_chats
            ]

    result = answer_career_question(
        request.question, user_skills=user_skills, conversation_history=conversation_history
    )

    # Conversation memory: persist every question+answer
    crud.log_mentor_chat(
        db, request.user_id, request.question, result["answer"], result["recommended_career"]
    )

    return schemas.MentorChatResponse(**result)


@app.get("/mentor/history/{user_id}")
def mentor_history(user_id: int, db: Session = Depends(get_db)):
    """Returns past mentor conversations for a logged-in user (conversation memory)."""
    history = crud.get_mentor_history(db, user_id)
    return [
        {"question": h.question, "answer": h.answer, "created_at": h.created_at}
        for h in history
    ]


# --------------------------------------------------------------------------
# Phase 10 - Deliverable 2: Dynamic Roadmap Generator
# --------------------------------------------------------------------------

@app.post("/roadmap/dynamic")
def dynamic_roadmap(request: schemas.DynamicRoadmapRequest):
    try:
        roadmap = generate_dynamic_roadmap(request.career, request.known_skills)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"career": request.career, "roadmap": roadmap}


# --------------------------------------------------------------------------
# Phase 10 - Deliverable 4: Resume vs Job Matching
# --------------------------------------------------------------------------

@app.post("/job-match", response_model=schemas.JobMatchResponse)
async def job_match(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    user_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a .pdf file")

    file_bytes = await file.read()
    try:
        resume_text = extract_text_from_pdf(file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    resume_skills = extract_skills(resume_text)
    job_result = extract_job_skills(job_description)
    job_skills = job_result["skills"]

    if not job_skills:
        # Even after direct matching AND career inference, nothing was found -
        # this means the job description is too short/vague to work with at
        # all (e.g. a single word). Ask for more detail rather than crash.
        raise HTTPException(
            status_code=422,
            detail=(
                "Couldn't extract any requirements from that job description - "
                "try pasting a longer excerpt with more detail about the role."
            ),
        )

    result = match_resume_to_job(resume_skills, job_skills)
    crud.log_job_match(db, user_id, result["match_score"], result["missing_keywords"])
    log_job_match(user_id, result["match_score"])

    response = schemas.JobMatchResponse(**result)
    if job_result["used_inference"]:
        response.note = (
            f"This job description didn't name specific tools, so we inferred "
            f"it's likely a {job_result['inferred_career']} role and matched "
            f"against that career's typical requirements."
        )
    return response


# --------------------------------------------------------------------------
# Phase 10 - Deliverable 5: Career Probability Engine
# --------------------------------------------------------------------------

@app.post("/career-probabilities", response_model=List[schemas.CareerProbability])
def career_probabilities(request: schemas.CareerProbabilityRequest):
    if not request.skills:
        raise HTTPException(status_code=400, detail="skills list cannot be empty")

    results = recommend_career(request.skills, None, top_n=8)
    return [
        schemas.CareerProbability(career=r["career"], probability=round(r["match_percent"], 1))
        for r in results
    ]


# --------------------------------------------------------------------------
# Phase 10 - Deliverable 6: AI Project Generator
# --------------------------------------------------------------------------

@app.post("/project-generator", response_model=schemas.ProjectGeneratorResponse)
def project_generator(request: schemas.ProjectGeneratorRequest, db: Session = Depends(get_db)):
    project = generate_project(request.domain, request.level)
    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"No project found for domain='{request.domain}', level='{request.level}'",
        )

    crud.log_project_recommendation(
        db, request.user_id, project["project_name"], project["domain"], project["difficulty"]
    )

    return schemas.ProjectGeneratorResponse(**project)


# --------------------------------------------------------------------------
# Phase 10 - Deliverable 7: Learning Time Predictor
# --------------------------------------------------------------------------

@app.post("/learning-time", response_model=schemas.LearningTimeResponse)
def learning_time(request: schemas.LearningTimeRequest):
    result = estimate_learning_time(request.career, request.current_skills)
    return schemas.LearningTimeResponse(**result)


# --------------------------------------------------------------------------
# Phase 10 - Deliverable 8: Analytics Dashboard
# --------------------------------------------------------------------------

@app.get("/analytics/summary", response_model=schemas.AnalyticsSummaryResponse)
def analytics_summary(db: Session = Depends(get_db)):
    data = crud.get_analytics_summary(db)
    return schemas.AnalyticsSummaryResponse(**data)


# --------------------------------------------------------------------------
# Phase 11 - internal helper: gathers everything needed for readiness
# scoring / career twin / companion, from real DB data only
# --------------------------------------------------------------------------

def _build_user_profile_context(db: Session, user_id: int) -> dict:
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"No user with id {user_id}")

    skills = crud.get_user_skills(db, user_id)
    completed_skill_names = [s.skill_name for s in skills if s.completed]
    remaining_skill_names = [s.skill_name for s in skills if not s.completed]
    total_skills = len(skills)

    projects = crud.get_user_projects(db, user_id)
    completed_project_names = [p.project_name for p in projects if p.completed]
    remaining_project_names = [p.project_name for p in projects if not p.completed]
    total_projects = len(projects)

    history = crud.get_resume_history(db, user_id)
    resume_score = history[-1].score if history else None

    job_match_score = crud.get_latest_job_match_score(db, user_id)

    return {
        "user": user,
        "career_goal": user.career_goal,
        "completed_skills": completed_skill_names,
        "remaining_skills": remaining_skill_names,
        "total_skills_count": total_skills,
        "completed_projects": completed_project_names,
        "remaining_projects": remaining_project_names,
        "total_projects_count": total_projects,
        "resume_score": resume_score,
        "job_match_score": job_match_score,
    }


# --------------------------------------------------------------------------
# Phase 11 - Deliverable 1 & 2: Career Twin + Readiness Score
# --------------------------------------------------------------------------

@app.get("/career-twin/{user_id}", response_model=schemas.CareerTwinResponse)
def career_twin(user_id: int, db: Session = Depends(get_db), current_user=Depends(verify_same_user_or_admin)):
    ctx = _build_user_profile_context(db, user_id)

    if not ctx["career_goal"]:
        raise HTTPException(
            status_code=400,
            detail="Set a career goal first (POST /users/{user_id}/goal) before generating a Career Twin.",
        )

    score_result = compute_readiness_score(
        target_career=ctx["career_goal"],
        completed_skills=ctx["completed_skills"],
        total_roadmap_skills=ctx["total_skills_count"],
        completed_roadmap_count=len(ctx["completed_skills"]),
        total_projects=ctx["total_projects_count"],
        completed_projects=len(ctx["completed_projects"]),
        latest_resume_score=ctx["resume_score"],
        latest_job_match_score=ctx["job_match_score"],
    )

    crud.upsert_career_profile(
        db, user_id, ctx["career_goal"], score_result["total"],
        len(ctx["completed_skills"]), len(ctx["completed_projects"]),
    )
    crud.add_score_snapshot_if_new_day(db, user_id, score_result["total"])

    return schemas.CareerTwinResponse(
        name=ctx["user"].name,
        target_career=ctx["career_goal"],
        current_skills=ctx["completed_skills"],
        readiness_score=score_result["total"],
        readiness_breakdown=score_result["breakdown"],
        resume_score=ctx["resume_score"],
        project_count=len(ctx["completed_projects"]),
        skill_count=len(ctx["completed_skills"]),
    )


# --------------------------------------------------------------------------
# Phase 11 - Deliverable 3: Career Simulator
# --------------------------------------------------------------------------

@app.post("/career-simulator", response_model=List[schemas.SimulatorStep])
def career_simulator(request: schemas.SimulatorRequest, db: Session = Depends(get_db)):
    ctx = _build_user_profile_context(db, request.user_id)
    if not ctx["career_goal"]:
        raise HTTPException(status_code=400, detail="Set a career goal first before simulating.")

    steps = simulate_learning_path(
        target_career=ctx["career_goal"],
        current_skills=ctx["completed_skills"],
        hypothetical_skills_in_order=request.hypothetical_skills,
        total_roadmap_skills=ctx["total_skills_count"],
        completed_roadmap_count=len(ctx["completed_skills"]),
        total_projects=ctx["total_projects_count"],
        completed_projects=len(ctx["completed_projects"]),
        latest_resume_score=ctx["resume_score"],
        latest_job_match_score=ctx["job_match_score"],
    )
    return steps


# --------------------------------------------------------------------------
# Phase 11 - Deliverable 4: Learning Analytics Engine (weekly report)
# --------------------------------------------------------------------------

@app.get("/learning-report/{user_id}", response_model=schemas.WeeklyReportResponse)
def learning_report(user_id: int, db: Session = Depends(get_db)):
    report = crud.get_weekly_report(db, user_id)
    return schemas.WeeklyReportResponse(**report)


# --------------------------------------------------------------------------
# Phase 11 - Deliverable 5: Recommendation Feedback Loop
# --------------------------------------------------------------------------

@app.post("/feedback")
def submit_feedback(request: schemas.FeedbackRequest, db: Session = Depends(get_db)):
    if not (1 <= request.rating <= 5):
        raise HTTPException(status_code=400, detail="rating must be between 1 and 5")
    row = crud.add_feedback(
        db, request.user_id, request.recommendation_type,
        request.reference, request.rating, request.comment,
    )
    return {"success": True, "feedback_id": row.id}


# --------------------------------------------------------------------------
# Phase 11 - Deliverable 6: Admin Analytics Dashboard
# --------------------------------------------------------------------------

@app.get("/admin/analytics", response_model=schemas.AdminAnalyticsResponse)
def admin_analytics(db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    data = crud.get_admin_analytics(db)
    return schemas.AdminAnalyticsResponse(**data)


# --------------------------------------------------------------------------
# Phase 11 - Deliverable 7: Notification Engine
# --------------------------------------------------------------------------

@app.get("/notifications/{user_id}", response_model=List[schemas.NotificationOut])
def notifications(user_id: int, db: Session = Depends(get_db)):
    crud.generate_notifications_if_needed(db, user_id)
    return crud.get_notifications(db, user_id)


@app.post("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    crud.mark_notification_read(db, notification_id)
    return {"success": True}


# --------------------------------------------------------------------------
# Phase 11 - Deliverable 8: AI Learning Companion
# --------------------------------------------------------------------------

@app.post("/companion/chat", response_model=schemas.CompanionChatResponse)
def companion_chat(request: schemas.CompanionChatRequest, db: Session = Depends(get_db)):
    ctx = _build_user_profile_context(db, request.user_id)

    roadmap_progress = (
        round((len(ctx["completed_skills"]) / ctx["total_skills_count"]) * 100)
        if ctx["total_skills_count"] else 0
    )

    context = {
        "career_goal": ctx["career_goal"],
        "roadmap_progress": roadmap_progress,
        "completed_skills_count": len(ctx["completed_skills"]),
        "total_skills_count": ctx["total_skills_count"],
        "remaining_skills": ctx["remaining_skills"],
        "completed_projects": ctx["completed_projects"],
        "remaining_projects": ctx["remaining_projects"],
        "resume_score": ctx["resume_score"],
        "resume_weaknesses": None,
    }

    past_chats = crud.get_mentor_history(db, request.user_id)
    conversation_history = (
        [{"question": c.question, "answer": c.answer} for c in past_chats] if past_chats else None
    )

    answer = answer_companion_question(request.question, context, conversation_history)
    crud.log_mentor_chat(db, request.user_id, request.question, answer, ctx["career_goal"])

    return schemas.CompanionChatResponse(answer=answer)


# --------------------------------------------------------------------------
# Phase 11 - Deliverable 9: Skill Graph
# --------------------------------------------------------------------------

@app.get("/skill-graph/{career}", response_model=schemas.SkillGraphResponse)
def skill_graph(career: str):
    graph = generate_skill_graph(career)
    if not graph["nodes"]:
        raise HTTPException(status_code=404, detail=f"No roadmap found for career '{career}'")
    return schemas.SkillGraphResponse(**graph)


# --------------------------------------------------------------------------
# Phase 11 - Deliverable 10: ML Recommendation Engine v2
# --------------------------------------------------------------------------

@app.post("/recommend-v2", response_model=List[schemas.RecommendV2Result])
def recommend_v2(request: schemas.RecommendV2Request):
    if not request.skills:
        raise HTTPException(status_code=400, detail="skills list cannot be empty")
    results = recommend_career_v2(request.skills, request.interest, top_n=5)
    return [schemas.RecommendV2Result(**r) for r in results]