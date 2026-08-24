
import tempfile
import os
import time
from typing import Optional, List

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from groq import Groq

from database.connection import get_db
from database.models import PracticeAttempt, Evaluation, Transcription, User, SuggestedQuestion
from backend.services.security import get_current_user
from ml.question_analyzer import analyze_question
from ml.rubric_builder import build_rubric
from config.settings import settings
from ml.coverage_engine import evaluate_concept_coverage
from ml.technical_checker import check_technical_accuracy
from ml.scoring_engine import compute_scores
from database.models import Topic
from ml.evaluation_service import run_evaluation
from database.models import Topic
from database.models import ProgressSnapshot

router = APIRouter(prefix="/practice", tags=["practice"])
groq_client = Groq(api_key=settings.GROQ_API_KEY)


# ---------------------------------------------------------------------------
# /practice/evaluate
# ---------------------------------------------------------------------------

class EvaluateRequest(BaseModel):
    topic_id: int
    question_text: str
    answer_text: str
    answer_mode: str            # "text" or "voice"
    source: str                  # "suggested" or "custom"
    transcription_id: Optional[int] = None


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

    # 2. Link any earlier voice transcription to this now-real attempt
    if payload.transcription_id:
        transcription = db.query(Transcription).filter(
            Transcription.id == payload.transcription_id
        ).first()
        if transcription:
            transcription.attempt_id = attempt.id

    
    existing_concepts = None
    if payload.source == "suggested":
        matching_question = db.query(SuggestedQuestion).filter(
            SuggestedQuestion.topic_id == payload.topic_id,
            SuggestedQuestion.question_text == payload.question_text,
        ).first()
        if matching_question:
            existing_concepts = matching_question.expected_concepts

    topic = db.query(Topic).filter(Topic.id == payload.topic_id).first()
    topic_name = topic.name if topic else ""

    result = run_evaluation(
        question_text=payload.question_text,
        answer_text=payload.answer_text,
        topic_name=topic_name,
        existing_concepts=existing_concepts,
    )

    latency_ms = int((time.time() - start_time) * 1000)

    evaluation = Evaluation(
        attempt_id=attempt.id,
        evaluator_version=result["evaluator_version"],
        overall_score=result["overall_score"],
        dimension_scores=result["dimension_scores"],
        feedback=result["feedback"],
        latency_ms=latency_ms,
    )
    db.add(evaluation)
    db.commit()

    _update_progress_snapshot(db, current_user.id, payload.topic_id, result["overall_score"])

    return EvaluationResponse(
        attempt_id=attempt.id,
        overall_score=result["overall_score"],
        dimension_scores=result["dimension_scores"],
        feedback=result["feedback"],
        answer_mode=payload.answer_mode,
        question_text=payload.question_text,
        answer_text=payload.answer_text,
    )

def _build_strengths(concept_results: list[dict]) -> list[str]:
    covered = [c["concept"] for c in concept_results if c["status"] == "covered"]
    if covered:
        return [f"Clearly addressed: {', '.join(covered)}."]
    return ["Answer submitted for evaluation."]


def _build_improvements(concept_results: list[dict], technical_flags: list[dict]) -> list[str]:
    improvements = []
    missing = [c["concept"] for c in concept_results if c["status"] == "missing"]
    if missing:
        improvements.append(f"Consider addressing: {', '.join(missing)}.")
    for flag in technical_flags:
        improvements.append(flag["explanation"])
    if not improvements:
        improvements.append("Good coverage — consider adding more depth or examples.")
    return improvements



def _update_progress_snapshot(db: Session, user_id: int, topic_id: int, new_score: int):
    """
    Updates (or creates) the user's progress snapshot for this topic —
    a running average score and attempt count, recalculated incrementally
    rather than by re-scanning every past attempt each time.
    """
    snapshot = db.query(ProgressSnapshot).filter(
        ProgressSnapshot.user_id == user_id,
        ProgressSnapshot.topic_id == topic_id,
    ).first()

    if snapshot:
        total_score = (snapshot.average_score * snapshot.attempts_count) + new_score
        snapshot.attempts_count += 1
        snapshot.average_score = round(total_score / snapshot.attempts_count)
    else:
        snapshot = ProgressSnapshot(
            user_id=user_id,
            topic_id=topic_id,
            average_score=new_score,
            attempts_count=1,
        )
        db.add(snapshot)

    db.commit()