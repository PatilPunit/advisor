from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from recommender import recommend_career
from roadmap import get_roadmap
from project_bank import get_projects_for_career

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