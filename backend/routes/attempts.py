from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from database.connection import get_db
from database.models import PracticeAttempt, Evaluation, Topic, User
from backend.services.security import get_current_user

router = APIRouter(prefix="/attempts", tags=["attempts"])


class AttemptSummary(BaseModel):
    attempt_id: int
    topic_name: str
    question_text: str
    answer_mode: str
    source: str
    overall_score: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class AttemptDetail(BaseModel):
    attempt_id: int
    topic_name: str
    question_text: str
    answer_text: str
    answer_mode: str
    source: str
    overall_score: Optional[int]
    dimension_scores: Optional[list]
    feedback: Optional[dict]
    created_at: datetime


@router.get("", response_model=List[AttemptSummary])
def list_attempts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Join attempts with their evaluation and topic name in one query
    results = (
        db.query(PracticeAttempt, Evaluation, Topic)
        .join(Evaluation, Evaluation.attempt_id == PracticeAttempt.id, isouter=True)
        .join(Topic, Topic.id == PracticeAttempt.topic_id)
        .filter(PracticeAttempt.user_id == current_user.id)
        .order_by(PracticeAttempt.created_at.desc())
        .all()
    )

    return [
        AttemptSummary(
            attempt_id=attempt.id,
            topic_name=topic.name,
            question_text=attempt.question_text,
            answer_mode=attempt.answer_mode,
            source=attempt.source,
            overall_score=evaluation.overall_score if evaluation else None,
            created_at=attempt.created_at,
        )
        for attempt, evaluation, topic in results
    ]


@router.get("/{attempt_id}", response_model=AttemptDetail)
def get_attempt(
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    attempt = (
        db.query(PracticeAttempt)
        .filter(PracticeAttempt.id == attempt_id, PracticeAttempt.user_id == current_user.id)
        .first()
    )
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    evaluation = db.query(Evaluation).filter(Evaluation.attempt_id == attempt.id).first()
    topic = db.query(Topic).filter(Topic.id == attempt.topic_id).first()

    return AttemptDetail(
        attempt_id=attempt.id,
        topic_name=topic.name if topic else "",
        question_text=attempt.question_text,
        answer_text=attempt.answer_text,
        answer_mode=attempt.answer_mode,
        source=attempt.source,
        overall_score=evaluation.overall_score if evaluation else None,
        dimension_scores=evaluation.dimension_scores if evaluation else None,
        feedback=evaluation.feedback if evaluation else None,
        created_at=attempt.created_at,
    )