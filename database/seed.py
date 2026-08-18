from database.connection import SessionLocal
from database.models import Topic, SuggestedQuestion

def seed():
    db = SessionLocal()

    if db.query(Topic).count() > 0:
        print("Topics already seeded, skipping.")
        db.close()
        return

    topics_data = {
        "ML": "Core machine learning concepts and algorithms.",
        "DL": "Deep learning, neural networks, and architectures.",
        "NLP": "Natural language processing techniques and models.",
        "Python": "Python programming fundamentals and best practices.",
        "SQL": "Relational databases and query writing.",
        "GenAI": "Generative AI, LLMs, and prompting.",
    }

    topic_objects = {}
    for name, desc in topics_data.items():
        topic = Topic(name=name, description=desc, active=True)
        db.add(topic)
        db.flush()  # assigns topic.id without committing yet
        topic_objects[name] = topic

    questions_data = [
        ("ML", "What is the bias-variance tradeoff?", "medium",
         ["bias", "variance", "underfitting", "overfitting", "model complexity"]),
        ("ML", "Explain how a random forest works.", "medium",
         ["decision trees", "bagging", "ensemble learning", "feature randomness"]),
        ("DL", "What is backpropagation?", "hard",
         ["gradient descent", "chain rule", "loss function", "weight update"]),
        ("DL", "What is the vanishing gradient problem?", "hard",
         ["deep networks", "activation functions", "gradient flow", "ReLU"]),
        ("NLP", "What is the difference between stemming and lemmatization?", "easy",
         ["word normalization", "morphology", "dictionary lookup"]),
        ("NLP", "How does attention work in transformers?", "hard",
         ["query key value", "self-attention", "context weighting", "transformers"]),
        ("Python", "What is the difference between a list and a tuple?", "easy",
         ["mutability", "data structures", "performance"]),
        ("Python", "Explain Python's GIL.", "medium",
         ["global interpreter lock", "threading", "concurrency", "multiprocessing"]),
        ("SQL", "What is the difference between INNER JOIN and LEFT JOIN?", "easy",
         ["joins", "relational tables", "null handling"]),
        ("SQL", "What is a database index and how does it improve performance?", "medium",
         ["indexing", "query optimization", "B-tree", "read/write tradeoff"]),
        ("GenAI", "What is the difference between fine-tuning and prompting?", "medium",
         ["fine-tuning", "prompt engineering", "model adaptation", "few-shot learning"]),
        ("GenAI", "What is RAG (Retrieval-Augmented Generation)?", "medium",
         ["retrieval", "embeddings", "vector search", "context injection"]),
    ]

    for topic_name, question_text, difficulty, concepts in questions_data:
        q = SuggestedQuestion(
            topic_id=topic_objects[topic_name].id,
            question_text=question_text,
            difficulty=difficulty,
            expected_concepts=concepts,
        )
        db.add(q)

    db.commit()
    db.close()
    print("Seeding complete.")

if __name__ == "__main__":
    seed()