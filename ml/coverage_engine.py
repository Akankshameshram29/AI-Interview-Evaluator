from ml.embedding_service import compute_similarity_matrix, split_into_sentences

# Thresholds — tuned conservatively; you'll calibrate these properly on Day 9
# against your labeled benchmark once real answers are being scored for real.
COVERED_THRESHOLD = 0.25
PARTIAL_THRESHOLD = 0.12


def evaluate_concept_coverage(rubric: list[dict], answer_text: str) -> list[dict]:
    """
    Given a rubric (list of {"concept": str, "weight": int}) and the answer text,
    returns a list of concept results:
    [{"concept": str, "weight": int, "status": "covered"|"partial"|"missing",
      "score": float, "evidence": str}]
    """
    if not rubric:
        return []

    concepts = [item["concept"] for item in rubric]
    sentences = split_into_sentences(answer_text)

    if not sentences:
        # No usable answer text at all — every concept is missing, no evidence
        return [
            {
                "concept": item["concept"],
                "weight": item["weight"],
                "status": "missing",
                "score": 0.0,
                "evidence": "",
            }
            for item in rubric
        ]

    similarity_matrix = compute_similarity_matrix(concepts, sentences)

    results = []
    for i, item in enumerate(rubric):
        concept_similarities = similarity_matrix[i]
        best_sentence_idx = int(concept_similarities.argmax())
        best_score = float(concept_similarities[best_sentence_idx])

        if best_score >= COVERED_THRESHOLD:
            status = "covered"
        elif best_score >= PARTIAL_THRESHOLD:
            status = "partial"
        else:
            status = "missing"

        evidence = sentences[best_sentence_idx] if status != "missing" else ""

        results.append({
            "concept": item["concept"],
            "weight": item["weight"],
            "status": status,
            "score": round(best_score, 3),
            "evidence": evidence,
        })

    return results