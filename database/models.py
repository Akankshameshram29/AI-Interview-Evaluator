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

class PracticeAttempt(Base):
    __tablename__ = "practice_attempts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    answer_mode = Column(String(20))   # 'text' or 'voice'
    answer_text = Column(Text)
    source = Column(String(20))         # 'suggested' or 'custom'
    created_at = Column(TIMESTAMP, server_default=func.now())

    evaluation = relationship("Evaluation", back_populates="attempt", uselist=False)


class Evaluation(Base):
    __tablename__ = "evaluations"
    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("practice_attempts.id"), nullable=False)
    evaluator_version = Column(String(50))
    overall_score = Column(Integer)     # 0-100, simple int for now
    dimension_scores = Column(JSON)     # e.g. {"correctness": 70, "completeness": 60}
    feedback = Column(JSON)             # structured feedback object
    latency_ms = Column(Integer)

    attempt = relationship("PracticeAttempt", back_populates="evaluation")

class Transcription(Base):
    __tablename__ = "transcriptions"
    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("practice_attempts.id"), nullable=True)
    transcript = Column(Text)
    stt_provider = Column(String(100))
    language = Column(String(20))
    stt_confidence = Column(Integer)  # store as 0-100 for simplicity
    created_at = Column(TIMESTAMP, server_default=func.now())

class ProgressSnapshot(Base):
    __tablename__ = "progress_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    average_score = Column(Integer)
    attempts_count = Column(Integer, default=0)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())