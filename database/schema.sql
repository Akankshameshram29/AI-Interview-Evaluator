CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE topics (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT TRUE
);

CREATE TABLE suggested_questions (
    id SERIAL PRIMARY KEY,
    topic_id INTEGER REFERENCES topics(id),
    question_text TEXT NOT NULL,
    difficulty VARCHAR(50),
    expected_concepts JSONB
);

CREATE TABLE practice_attempts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    topic_id INTEGER REFERENCES topics(id),
    question_text TEXT NOT NULL,
    answer_mode VARCHAR(20),      -- 'text' or 'voice'
    answer_text TEXT,
    source VARCHAR(20),            -- 'suggested' or 'custom'
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE transcriptions (
    id SERIAL PRIMARY KEY,
    attempt_id INTEGER REFERENCES practice_attempts(id),
    transcript TEXT,
    stt_provider VARCHAR(100),
    language VARCHAR(20),
    stt_confidence FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE evaluations (
    id SERIAL PRIMARY KEY,
    attempt_id INTEGER REFERENCES practice_attempts(id),
    evaluator_version VARCHAR(50),
    overall_score FLOAT,
    dimension_scores JSONB,
    feedback JSONB,
    latency_ms INTEGER
);

CREATE TABLE concept_results (
    id SERIAL PRIMARY KEY,
    evaluation_id INTEGER REFERENCES evaluations(id),
    concept VARCHAR(255),
    status VARCHAR(20),   -- 'covered', 'partial', 'missing'
    score FLOAT,
    evidence TEXT
);

CREATE TABLE progress_snapshots (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    topic_id INTEGER REFERENCES topics(id),
    average_score FLOAT,
    attempts_count INTEGER,
    updated_at TIMESTAMP DEFAULT NOW()
);