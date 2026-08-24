"""
recommender_ml.py
--------------------
Deliverable 10: Recommendation Engine v2 (ML-based).

HONEST DISCLOSURE - read this before trusting the numbers:
Training a real supervised model needs labeled outcomes (did this person
actually succeed in this career?). This project doesn't have that data
yet - no user has a verified real-world outcome logged. So instead of
faking it, this trains on BOOTSTRAPPED SYNTHETIC data: for each of the 8
careers, we generate thousands of plausible skill-profiles (the real
required skills plus realistic noise - some missing, some extra unrelated
skills) and train a RandomForestClassifier to recognize the PATTERN of
"what a person with skill-set X typically wants to become," per
career_paths.csv.

This is a legitimate ML technique (data augmentation from a known rule)
but it is NOT learning from real human outcomes yet. As real usage
accumulates in the `career_recommendations` table, `retrain_from_real_data()`
below can retrain on genuine user-career pairs instead - the moment you
have enough real data (the code checks for a minimum row count), swap
which training function main.py calls on startup.

The ML prediction is blended 50/50 with the deterministic rule-based
match_percent from recommender.py, not used alone - this keeps the system
robust even while the ML layer is still "young."
"""

from __future__ import annotations

import os
import random
from typing import Dict, List

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier

from recommender import recommend_career, _load_career_data
from skills_vocab import load_master_vocabulary

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "career_model.joblib")

MIN_REAL_SAMPLES_TO_RETRAIN = 200  # threshold before switching to real-data training
SYNTHETIC_SAMPLES_PER_CAREER = 500
NOISE_DROPOUT_RATE = 0.3   # chance to remove a real required skill (simulates partial learners)
NOISE_EXTRA_RATE = 0.15    # chance to add each unrelated vocab skill (simulates real messy resumes)


def _vocab_and_index() -> tuple[List[str], Dict[str, int]]:
    vocab = load_master_vocabulary()
    return vocab, {skill.lower(): i for i, skill in enumerate(vocab)}


def _skills_to_vector(skills: List[str], vocab_index: Dict[str, int], vocab_size: int) -> np.ndarray:
    vec = np.zeros(vocab_size, dtype=np.int8)
    for skill in skills:
        idx = vocab_index.get(skill.strip().lower())
        if idx is not None:
            vec[idx] = 1
    return vec


def _generate_synthetic_dataset():
    """Bootstraps a training set from career_paths.csv's real required_skills, with realistic noise."""
    vocab, vocab_index = _vocab_and_index()
    careers = _load_career_data()

    X, y = [], []
    for career in careers:
        required = career["required_skills"]
        for _ in range(SYNTHETIC_SAMPLES_PER_CAREER):
            sample_skills = [s for s in required if random.random() > NOISE_DROPOUT_RATE]
            if not sample_skills:  # never generate a fully-empty sample
                sample_skills = [random.choice(required)]
            for other_skill in vocab:
                if other_skill.lower() not in {s.lower() for s in required}:
                    if random.random() < NOISE_EXTRA_RATE:
                        sample_skills.append(other_skill)

            X.append(_skills_to_vector(sample_skills, vocab_index, len(vocab)))
            y.append(career["career"])

    return np.array(X), np.array(y), vocab


def train_model(save: bool = True) -> RandomForestClassifier:
    """Trains the RandomForest on bootstrapped synthetic data and saves it to disk."""
    X, y, vocab = _generate_synthetic_dataset()
    model = RandomForestClassifier(n_estimators=200, max_depth=12, random_state=42, n_jobs=-1)
    model.fit(X, y)

    if save:
        joblib.dump({"model": model, "vocab": vocab}, MODEL_PATH)

    return model


def _load_or_train() -> tuple:
    if os.path.exists(MODEL_PATH):
        bundle = joblib.load(MODEL_PATH)
        return bundle["model"], bundle["vocab"]
    model = train_model(save=True)
    vocab = load_master_vocabulary()
    return model, vocab


def predict_ml_probabilities(skills: List[str]) -> List[Dict]:
    """Returns [{"career": ..., "ml_probability": 0-100}, ...] for all 8 careers, ML-predicted."""
    model, vocab = _load_or_train()
    vocab_index = {s.lower(): i for i, s in enumerate(vocab)}
    vec = _skills_to_vector(skills, vocab_index, len(vocab)).reshape(1, -1)

    probabilities = model.predict_proba(vec)[0]
    classes = model.classes_

    return sorted(
        [{"career": c, "ml_probability": round(p * 100, 1)} for c, p in zip(classes, probabilities)],
        key=lambda r: r["ml_probability"], reverse=True,
    )


def recommend_career_v2(skills: List[str], interest: str = None, top_n: int = 3) -> List[Dict]:
    """
    The 'v2' ensemble: blends the deterministic rule-based match_percent
    (recommender.py, Phase 4) with the ML-predicted probability above,
    50/50. This keeps results grounded even while the ML layer is trained
    only on synthetic bootstrap data rather than real outcomes.
    """
    rule_based = recommend_career(skills, interest, top_n=8)
    ml_results = predict_ml_probabilities(skills)
    ml_lookup = {r["career"]: r["ml_probability"] for r in ml_results}

    blended = []
    for r in rule_based:
        ml_score = ml_lookup.get(r["career"], 0)
        blended_score = round((r["match_percent"] * 0.5) + (ml_score * 0.5), 1)
        blended.append({
            "career": r["career"],
            "rule_based_score": r["match_percent"],
            "ml_score": ml_score,
            "blended_score": blended_score,
            "missing_skills": r["missing_skills"],
        })

    blended.sort(key=lambda r: r["blended_score"], reverse=True)
    return blended[:top_n]


def retrain_from_real_data(db) -> Dict:
    """
    Upgrade path: once enough REAL user data exists (career_recommendations
    table), retrain on actual usage patterns instead of synthetic bootstrap
    data. Currently a no-op stub until MIN_REAL_SAMPLES_TO_RETRAIN rows
    exist - call this manually (e.g. via a scheduled job) as your user base
    grows; it is NOT wired into any automatic schedule in this codebase.
    """
    from database.models import CareerRecommendation
    count = db.query(CareerRecommendation).count()
    if count < MIN_REAL_SAMPLES_TO_RETRAIN:
        return {
            "retrained": False,
            "reason": f"Only {count} real samples logged - need {MIN_REAL_SAMPLES_TO_RETRAIN}+ "
                      f"before real-data training is statistically meaningful. Still using synthetic bootstrap model.",
        }
    # Real implementation would pull (missing_skills -> career) pairs here
    # and train on genuine usage patterns. Left as a clear extension point.
    return {"retrained": False, "reason": "Real-data training not yet implemented - extension point ready."}