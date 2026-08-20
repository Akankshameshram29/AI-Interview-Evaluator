
import tempfile
import os
import time
from typing import Optional, List

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database.connection import get_db
from database.models import PracticeAttempt, Evaluation, Transcription, User
from backend.services.security import get_current_user

router = APIRouter(prefix="/practice", tags=["practice"])

from groq import Groq
from config.settings import settings

groq_client = Groq(api_key=settings.GROQ_API_KEY)

MAX_RECORDING_SECONDS = 5 * 60  # 5 minutes



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

    # 2. If this answer came from a voice recording, link its transcription
    #    row (created earlier, with attempt_id=None) to this real attempt
    if payload.transcription_id:
        transcription = db.query(Transcription).filter(
            Transcription.id == payload.transcription_id
        ).first()
        if transcription:
            transcription.attempt_id = attempt.id

    # 3. STUB evaluation — fixed dummy scoring, replaced by real ML on Days 6-9
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


# ---------------------------------------------------------------------------
# /practice/transcribe
# ---------------------------------------------------------------------------

class TranscribeResponse(BaseModel):
    transcription_id: int
    transcript: str
    language: Optional[str]
    confidence: Optional[int]


@router.post("/transcribe", response_model=TranscribeResponse)
def transcribe_audio(
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Save uploaded audio to a temp file (faster-whisper needs a file path, not raw bytes)
    suffix = os.path.splitext(audio.filename or "audio.wav")[1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio.file.read())
        tmp_path = tmp.name

    try:
        # Basic size guard against absurdly long/corrupt recordings
        file_size_mb = os.path.getsize(tmp_path) / (1024 * 1024)
        if file_size_mb > 50:
            raise HTTPException(status_code=400, detail="Recording too long or file too large.")

        try:
            with open(tmp_path, "rb") as audio_file:
                transcription_result = groq_client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-large-v3-turbo",  # fast + accurate
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
        # Always delete the temp audio file, whether transcription succeeded or failed
        if os.path.exists(tmp_path):
            os.remove(tmp_path)