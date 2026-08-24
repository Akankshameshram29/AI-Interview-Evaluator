from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime

from database.connection import get_db
from database.models import ProgressSnapshot, Topic, User
from backend.services.security import get_current_user

router = APIRouter(prefix="/progress", tags=["progress"])


class ProgressItem(BaseModel):
    topic_name: str
    average_score: float
    attempts_count: int
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[ProgressItem])
def get_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    results = (
        db.query(ProgressSnapshot, Topic)
        .join(Topic, Topic.id == ProgressSnapshot.topic_id)
        .filter(ProgressSnapshot.user_id == current_user.id)
        .all()
    )

    return [
        ProgressItem(
            topic_name=topic.name,
            average_score=snapshot.average_score,
            attempts_count=snapshot.attempts_count,
            updated_at=snapshot.updated_at,
        )
        for snapshot, topic in results
    ]