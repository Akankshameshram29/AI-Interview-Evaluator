
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

    # 3. Derive expected concepts and build the rubric
    existing_concepts = None
    if payload.source == "suggested":
        matching_question = db.query(SuggestedQuestion).filter(
            SuggestedQuestion.topic_id == payload.topic_id,
            SuggestedQuestion.question_text == payload.question_text,
        ).first()
        if matching_question:
            existing_concepts = matching_question.expected_concepts

    
    concepts = analyze_question(payload.question_text, existing_concepts)
    rubric = build_rubric(concepts)

        # 4. Real concept coverage
    concept_results = evaluate_concept_coverage(rubric, payload.answer_text)

    # 5. Technical accuracy checks — need the topic's name for the misconception lookup
    topic = db.query(Topic).filter(Topic.id == payload.topic_id).first()
    topic_name = topic.name if topic else ""
    technical_flags = check_technical_accuracy(payload.answer_text, topic_name)

    # 6. Real scoring — replaces the Day 6/7 provisional placeholder entirely
    scores = compute_scores(concept_results, technical_flags, payload.answer_text)
    overall_score = scores["overall_score"]
    dimension_scores_list = scores["dimension_scores"]

    covered_count = sum(1 for c in concept_results if c["status"] == "covered")

    feedback = {
        "strengths": _build_strengths(concept_results),
        "improvements": _build_improvements(concept_results, technical_flags),
        "concept_results": concept_results,
        "technical_flags": technical_flags,
        "rubric": rubric,
    }
    latency_ms = int((time.time() - start_time) * 1000)

    evaluation = Evaluation(
        attempt_id=attempt.id,
        evaluator_version="scoring-v1",   # bumped again — real scoring engine now live
        overall_score=overall_score,
        dimension_scores=dimension_scores_list,
        feedback=feedback,
        latency_ms=latency_ms,
    )
    db.add(evaluation)
    db.commit()

    return EvaluationResponse(
        attempt_id=attempt.id,
        overall_score=overall_score,
        dimension_scores=dimension_scores_list,
        feedback=feedback,
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