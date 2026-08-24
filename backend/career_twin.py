"""
career_twin.py
-----------------
Deliverable 1: Career Twin (digital career profile)
Deliverable 2: Career Readiness Score
Deliverable 3: Career Simulator

The Readiness Score is a weighted blend of 5 real, measurable factors -
not a single number pulled from one source. This is deliberately designed
so every point is explainable: a user can see exactly why they're at
72/100 and exactly what to do to move the needle.

    Skills   : 30 pts - how many of the TARGET career's required skills you have
    Projects : 25 pts - completed / total tracked projects
    Resume   : 15 pts - your latest resume intelligence score
    Roadmap  : 20 pts - completed / total roadmap steps (finer-grained than Skills)
    Job Match: 10 pts - your most recent resume-vs-job-description match score

Skills vs Roadmap are deliberately different signals: Skills measures fit
against the career's CORE requirements (career_paths.csv, ~5 items),
Roadmap measures progress through the full learning path (skill_roadmap.csv,
often 7+ finer-grained steps) - so a user can be "ready on core skills" but
still mid-roadmap, or vice versa.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from recommender import recommend_career
from roadmap1 import get_roadmap, generate_dynamic_roadmap

WEIGHTS = {"skills": 30, "projects": 25, "resume": 15, "roadmap": 20, "job_match": 10}


def compute_readiness_score(
    target_career: str,
    completed_skills: List[str],
    total_roadmap_skills: int,
    completed_roadmap_count: int,
    total_projects: int,
    completed_projects: int,
    latest_resume_score: Optional[int],
    latest_job_match_score: Optional[int],
) -> Dict:
    """
    Returns the full breakdown, not just a total - so the UI can show
    "Skills: 18/30, Projects: 12/25, ..." exactly like the spec's example.
    """
    # Skills: career-fit % against the career's CORE required skills
    if completed_skills:
        results = recommend_career(completed_skills, target_career, top_n=8)
        match = next((r for r in results if r["career"].lower() == target_career.lower()), None)
        skill_fit_pct = match["match_percent"] if match else 0
    else:
        skill_fit_pct = 0
    skills_points = round(WEIGHTS["skills"] * (skill_fit_pct / 100))

    # Roadmap: finer-grained progress through the full learning path
    roadmap_pct = (completed_roadmap_count / total_roadmap_skills * 100) if total_roadmap_skills else 0
    roadmap_points = round(WEIGHTS["roadmap"] * (roadmap_pct / 100))

    # Projects
    project_pct = (completed_projects / total_projects * 100) if total_projects else 0
    project_points = round(WEIGHTS["projects"] * (project_pct / 100))

    # Resume
    resume_points = round(WEIGHTS["resume"] * ((latest_resume_score or 0) / 100))

    # Job match
    job_match_points = round(WEIGHTS["job_match"] * ((latest_job_match_score or 0) / 100))

    total = skills_points + roadmap_points + project_points + resume_points + job_match_points

    return {
        "total": total,
        "breakdown": {
            "skills": {"points": skills_points, "max": WEIGHTS["skills"]},
            "projects": {"points": project_points, "max": WEIGHTS["projects"]},
            "resume": {"points": resume_points, "max": WEIGHTS["resume"]},
            "roadmap": {"points": roadmap_points, "max": WEIGHTS["roadmap"]},
            "job_match": {"points": job_match_points, "max": WEIGHTS["job_match"]},
        },
    }


def simulate_learning_path(
    target_career: str,
    current_skills: List[str],
    hypothetical_skills_in_order: List[str],
    total_roadmap_skills: int,
    completed_roadmap_count: int,
    total_projects: int,
    completed_projects: int,
    latest_resume_score: Optional[int],
    latest_job_match_score: Optional[int],
) -> List[Dict]:
    """
    Deliverable 3: Career Simulator - "what happens if I learn X, then Y?"

    Only the Skills and Roadmap components change as hypothetical skills
    are added (resume score and job match score wouldn't retroactively
    improve just from knowing a skill you haven't documented anywhere yet -
    holding them constant keeps the simulation honest rather than
    over-promising).

    Returns an ordered list: [{"label": "Current", "score": 72}, {"label":
    "After Machine Learning", "score": 81}, ...]
    """
    full_roadmap = {s.lower() for s in get_roadmap(target_career)}
    running_skills = list(current_skills)
    running_roadmap_count = completed_roadmap_count

    steps = []

    baseline = compute_readiness_score(
        target_career, running_skills, total_roadmap_skills, running_roadmap_count,
        total_projects, completed_projects, latest_resume_score, latest_job_match_score,
    )
    steps.append({"label": "Current", "score": baseline["total"], "skill_added": None})

    for skill in hypothetical_skills_in_order:
        if skill.lower() not in {s.lower() for s in running_skills}:
            running_skills.append(skill)
        if skill.lower() in full_roadmap:
            running_roadmap_count = min(running_roadmap_count + 1, total_roadmap_skills)

        result = compute_readiness_score(
            target_career, running_skills, total_roadmap_skills, running_roadmap_count,
            total_projects, completed_projects, latest_resume_score, latest_job_match_score,
        )
        steps.append({"label": f"After {skill}", "score": result["total"], "skill_added": skill})

    return steps