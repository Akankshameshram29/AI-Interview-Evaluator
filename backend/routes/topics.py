from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from database.connection import get_db
from database.models import Topic, SuggestedQuestion

router = APIRouter(prefix="/topics", tags=["topics"])

class TopicResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True  # lets Pydantic read SQLAlchemy objects directly

class QuestionResponse(BaseModel):
    id: int
    question_text: str
    difficulty: Optional[str]
    expected_concepts: Optional[List[str]]

    class Config:
        from_attributes = True

@router.get("", response_model=List[TopicResponse])
def get_topics(db: Session = Depends(get_db)):
    topics = db.query(Topic).filter(Topic.active == True).all()
    return topics

@router.get("/{topic_id}/questions", response_model=List[QuestionResponse])
def get_questions(topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    questions = db.query(SuggestedQuestion).filter(
        SuggestedQuestion.topic_id == topic_id
    ).all()
    return questions