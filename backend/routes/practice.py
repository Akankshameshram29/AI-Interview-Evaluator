
import tempfile
import os
import time
from typing import Optional, List

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from groq import Groq
from backend.limiter import limiter
from fastapi import Request

from database.connection import get_db
from database.models import (
    PracticeAttempt,
    Evaluation,
    Transcription,
    User,
    SuggestedQuestion,
    Topic,
    ProgressSnapshot,
)
from backend.services.security import get_current_user
from ml.evaluation_service import run_evaluation
from config.settings import settings

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
@limiter.limit("10/minute")
def evaluate_answer(
    request: Request,
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

    # 3. Look up expected_concepts if this is a suggested question
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

    # 4. Run the full evaluation pipeline (analyzer -> rubric -> coverage -> checks -> scoring -> feedback)
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


# ---------------------------------------------------------------------------
# /practice/transcribe
# ---------------------------------------------------------------------------

class TranscribeResponse(BaseModel):
    transcription_id: int
    transcript: str
    language: Optional[str]
    confidence: Optional[int]


def validate_audio_file_size(file_size_mb: float, max_size_mb: float = 50) -> None:
    """Raises HTTPException if file is too large. Extracted as its own
    function so it can be unit-tested in isolation (Day 11)."""
    if file_size_mb > max_size_mb:
        raise HTTPException(status_code=400, detail="Recording too long or file too large.")


@router.post("/transcribe", response_model=TranscribeResponse)
@limiter.limit("10/minute")
def transcribe_audio(
    request: Request,
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Save uploaded audio to a temp file, then send it to Groq's hosted Whisper API
    suffix = os.path.splitext(audio.filename or "audio.wav")[1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio.file.read())
        tmp_path = tmp.name

    try:
        file_size_mb = os.path.getsize(tmp_path) / (1024 * 1024)
        validate_audio_file_size(file_size_mb)

        try:
            with open(tmp_path, "rb") as audio_file:
                transcription_result = groq_client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-large-v3-turbo",
                )
            transcript_text = transcription_result.text.strip()
            detected_language = None
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=503, detail="Speech-to-text service unavailable. Please try again.")

        if not transcript_text:
            raise HTTPException(status_code=422, detail="No speech detected. Please try recording again.")

        transcription = Transcription(
            attempt_id=None,  # linked later, at evaluate time
            transcript=transcript_text,
            stt_provider="groq-whisper-large-v3-turbo",
            language=detected_language,
            stt_confidence=None,
        )
        db.add(transcription)
        db.commit()
        db.refresh(transcription)

        return TranscribeResponse(
            transcription_id=transcription.id,
            transcript=transcript_text,
            language=detected_language,
            confidence=None,
        )

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def validate_audio_file_size(file_size_mb: float, max_size_mb: float = 50) -> None:
    """Raises HTTPException if file is too large. Extracted for testability."""
    if file_size_mb > max_size_mb:
        raise HTTPException(status_code=400, detail="Recording too long or file too large.")