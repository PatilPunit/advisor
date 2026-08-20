from typing import List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from recommender import recommend_career
from roadmap import get_roadmap
from project import get_projects_for_career
from resume.parser import extract_text_from_pdf
from resume.extractor import extract_skills
from resume.scorer import calculate_score

app = FastAPI(title="AI Career Advisor")

# Allow the Vite dev server (and any origin, for now) to call this API.
# Tighten allow_origins to your real frontend URL before deploying.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------
# Request / Response models
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
# Routes
# --------------------------------------------------------------------------

@app.get("/")
def home():
    return {"message": "AI Career Advisor Running"}


@app.post("/recommend", response_model=RecommendResponse)
def recommend(request: RecommendRequest):
    if not request.skills:
        raise HTTPException(status_code=400, detail="skills list cannot be empty")

    # Rank the top 3 careers (uses your recommender.py logic as-is)
    results = recommend_career(request.skills, request.interest, top_n=3)
    if not results:
        raise HTTPException(status_code=404, detail="No matching career found")

    top = results[0]

    # Ordered skill roadmap for the top career (roadmap.py)
    roadmap = get_roadmap(top["career"])

    # Beginner + advanced projects, enriched with domain/difficulty (project_bank.py)
    projects = get_projects_for_career(
        top["beginner_project"], top["advanced_project"]
    )

    # Top 3 career matches, for the Career Match Cards row
    top_matches = [
        TopMatch(career=r["career"], score=round(r["match_percent"]))
        for r in results[:3]
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
async def resume_analyze(file: UploadFile = File(...)):
    # --- Validate the upload is actually a PDF ---
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a .pdf file")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # --- STEP 3: Read PDF -> full text ---
    try:
        resume_text = extract_text_from_pdf(file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not resume_text.strip():
        raise HTTPException(
            status_code=422,
            detail="No readable text found in this PDF (it may be a scanned image).",
        )

    # --- STEP 4: Extract skills mentioned anywhere in the resume ---
    detected_skills = extract_skills(resume_text)
    if not detected_skills:
        raise HTTPException(
            status_code=422,
            detail="No recognizable skills found in this resume.",
        )

    # --- Determine best-fit career using the existing recommender logic ---
    # (Reuses recommend_career instead of hardcoding one target career -
    # the resume is scored against whichever career it's the strongest fit for.)
    top_career_result = recommend_career(detected_skills, interest=None, top_n=1)[0]
    recommended_career = top_career_result["career"]
    required_skills = top_career_result["required_skills"]

    # --- STEP 5: Score = detected / required * 100 ---
    score_result = calculate_score(detected_skills, required_skills)

    return ResumeAnalyzeResponse(
        score=score_result["score"],
        skills=detected_skills,
        missing=score_result["missing"],
        recommended_career=recommended_career,
    )