from ml.coverage_engine import evaluate_concept_coverage


def test_coverage_empty_rubric_returns_empty():
    assert evaluate_concept_coverage([], "some answer text") == []


def test_coverage_empty_answer_marks_everything_missing():
    rubric = [{"concept": "bias", "weight": 100}]
    results = evaluate_concept_coverage(rubric, "")
    assert results[0]["status"] == "missing"
    assert results[0]["evidence"] == ""


def test_coverage_strong_match_scores_higher_than_weak_match():
    rubric = [{"concept": "bias variance tradeoff", "weight": 100}]
    strong_answer = "The bias variance tradeoff is a key concept in machine learning."
    weak_answer = "I like pizza and long walks on the beach."

    strong_result = evaluate_concept_coverage(rubric, strong_answer)
    weak_result = evaluate_concept_coverage(rubric, weak_answer)

    assert strong_result[0]["score"] > weak_result[0]["score"]