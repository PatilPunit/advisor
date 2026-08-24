"""
skill_graph.py
-----------------
Deliverable 9: Skill Graph - a visual dependency tree for a career's
learning path.

Your skill_roadmap.csv is a flat ordered list (1. Python, 2. NumPy, ...).
A real learning path isn't strictly linear though - several skills often
branch off a shared foundation before converging into a chain (exactly
like the spec's example: Python -> NumPy/Pandas/Statistics in parallel,
then Statistics -> ML -> Deep Learning as a chain).

This module auto-derives a reasonable branching structure from the flat
CSV order using a simple, transparent heuristic (documented below) rather
than hand-authoring a graph per career - so it scales to every career in
your dataset, including ones you add later, with zero extra maintenance.
"""

from __future__ import annotations

from typing import Dict, List

from roadmap import get_roadmap

# How many of the earliest roadmap skills are treated as parallel
# foundational branches off the root, before the rest chain sequentially.
FOUNDATION_BRANCH_COUNT = 3


def generate_skill_graph(career: str) -> Dict:
    """
    Heuristic: the first skill is the root. The next FOUNDATION_BRANCH_COUNT
    skills are treated as parallel children of the root (foundational skills
    usually learned in any order once the root is known). Every skill after
    that chains linearly from the last foundational skill - approximating
    how advanced topics (ML, Deep Learning) build on earlier fundamentals
    rather than on each other in parallel.

    Returns:
        {
          "nodes": ["Python", "NumPy", "Pandas", "Statistics", "Machine Learning", ...],
          "edges": [{"from": "Python", "to": "NumPy"}, {"from": "Python", "to": "Pandas"}, ...]
        }
    """
    skills = get_roadmap(career)
    if not skills:
        return {"nodes": [], "edges": []}

    if len(skills) == 1:
        return {"nodes": skills, "edges": []}

    root = skills[0]
    foundation = skills[1:1 + FOUNDATION_BRANCH_COUNT]
    remainder = skills[1 + FOUNDATION_BRANCH_COUNT:]

    edges = [{"from": root, "to": skill} for skill in foundation]

    # Chain the remainder starting from the last foundational skill (or
    # root itself if there were no foundation skills, e.g. very short roadmaps)
    chain_start = foundation[-1] if foundation else root
    prev = chain_start
    for skill in remainder:
        edges.append({"from": prev, "to": skill})
        prev = skill

    return {"nodes": skills, "edges": edges}