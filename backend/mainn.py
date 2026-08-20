from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from recommender import recommend_career
from roadmap import get_roadmap
from project import get_projects_for_career

app = FastAPI(title="AI Career Advisor")


# --------------------------------------------------------------------------
# Request / Response models
# --------------------------------------------------------------------------

class RecommendRequest(BaseModel):
    skills: List[str] = Field(..., example=["Python", "Pandas"])
    interest: Optional[str] = Field(None, example="cybersecurity analyst")


class RecommendResponse(BaseModel):
    career: str
    match_score: float
    missing_skills: List[str]
    roadmap: List[str]
    projects: List[dict]


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

    # Top recommended career (uses your recommender.py logic as-is)
    results = recommend_career(request.skills, request.interest, top_n=1)
    if not results:
        raise HTTPException(status_code=404, detail="No matching career found")

    top = results[0]

    # Ordered skill roadmap for that career (roadmap.py)
    roadmap = get_roadmap(top["career"])

    # Beginner + advanced projects, enriched with domain/difficulty (project_bank.py)
    projects = get_projects_for_career(
        top["beginner_project"], top["advanced_project"]
    )

    return RecommendResponse(
        career=top["career"],
        match_score=top["match_percent"],
        missing_skills=top["missing_skills"],
        roadmap=roadmap,
        projects=projects,
    )