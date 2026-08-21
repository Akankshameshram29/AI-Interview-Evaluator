from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def compute_similarity_matrix(concepts: list[str], sentences: list[str]) -> np.ndarray:
    """
    Given a list of rubric concepts and a list of answer sentences,
    returns a matrix of similarity scores (concepts x sentences).
    Each value is between 0 and 1 — higher means more similar.
    """
    if not concepts or not sentences:
        return np.zeros((len(concepts), len(sentences)))

    # Fit TF-IDF on the combined vocabulary of concepts + sentences together,
    # so both sides are represented in the same vector space
    all_texts = concepts + sentences
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))

    try:
        tfidf_matrix = vectorizer.fit_transform(all_texts)
    except ValueError:
        # Happens if all_texts is empty or contains only stopwords
        return np.zeros((len(concepts), len(sentences)))

    concept_vectors = tfidf_matrix[:len(concepts)]
    sentence_vectors = tfidf_matrix[len(concepts):]

    return cosine_similarity(concept_vectors, sentence_vectors)


def split_into_sentences(text: str) -> list[str]:
    """
    Simple sentence splitter — good enough for interview-answer-length text.
    Splits on '.', '!', '?' followed by whitespace, filters out empty fragments.
    """
    import re
    raw_sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in raw_sentences if s.strip()]