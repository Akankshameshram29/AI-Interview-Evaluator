from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean, Text, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())

class Topic(Base):
    __tablename__ = "topics"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    active = Column(Boolean, default=True)

    questions = relationship("SuggestedQuestion", back_populates="topic")


class SuggestedQuestion(Base):
    __tablename__ = "suggested_questions"
    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    difficulty = Column(String(50))
    expected_concepts = Column(JSON)  # list of strings, e.g. ["overfitting", "bias-variance tradeoff"]

    topic = relationship("Topic", back_populates="questions")