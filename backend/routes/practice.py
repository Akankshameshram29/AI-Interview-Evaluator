from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import time

from database.connection import get_db
from database.models import PracticeAttempt, Evaluation, User
from backend.services.security import get_current_user

router = APIRouter(prefix="/practice", tags=["practice"])

class EvaluateRequest(BaseModel):
    topic_id: int
    question_text: str
    answer_text: str
    answer_mode: str   # "text" or "voice"
    source: str         # "suggested" or "custom"

class DimensionScore(BaseModel):
    dimension: str
    score: int

class EvaluationResponse(BaseModel):
    attempt_id: int
    overall_score: int
    dimension_scores: List[DimensionScore]
    feedback: dict
    answer_mode: str
    question_text: str
    answer_text: str

@router.post("/evaluate", response_model=EvaluationResponse)
def evaluate_answer(
    payload: EvaluateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start_time = time.time()

    # 1. Save the attempt, scoped to the authenticated user
    attempt = PracticeAttempt(
        user_id=current_user.id,
        topic_id=payload.topic_id,
        question_text=payload.question_text,
        answer_mode=payload.answer_mode,
        answer_text=payload.answer_text,
        source=payload.source,
    )
    db.add(attempt)
    db.flush()  # get attempt.id without committing yet

    # 2. STUB evaluation — fixed dummy scoring, replaced by real ML on Days 6-9
    stub_dimension_scores = [
        {"dimension": "correctness", "score": 70},
        {"dimension": "completeness", "score": 60},
        {"dimension": "clarity", "score": 80},
    ]
    stub_overall = 70
    stub_feedback = {
        "strengths": ["Answer addresses the core question."],
        "improvements": ["This is placeholder feedback — real evaluation coming soon."],
        "concept_coverage": "Not yet analyzed (stub).",
    }
    latency_ms = int((time.time() - start_time) * 1000)

    evaluation = Evaluation(
        attempt_id=attempt.id,
        evaluator_version="stub-v0",
        overall_score=stub_overall,
        dimension_scores=stub_dimension_scores,
        feedback=stub_feedback,
        latency_ms=latency_ms,
    )
    db.add(evaluation)
    db.commit()

    return EvaluationResponse(
        attempt_id=attempt.id,
        overall_score=stub_overall,
        dimension_scores=stub_dimension_scores,
        feedback=stub_feedback,
        answer_mode=payload.answer_mode,
        question_text=payload.question_text,
        answer_text=payload.answer_text,
    )