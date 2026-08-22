# ml/evaluation_service.py

from ml.question_analyzer import analyze_question
from ml.rubric_builder import build_rubric
from ml.coverage_engine import evaluate_concept_coverage
from ml.technical_checker import check_technical_accuracy
from ml.scoring_engine import compute_scores
from ml.feedback_generator import generate_feedback

EVALUATOR_VERSION = "eval-v2"


def run_evaluation(
    question_text: str,
    answer_text: str,
    topic_name: str,
    existing_concepts: list[str] | None = None,
) -> dict:
    """
    Runs the full evaluation pipeline: analyze -> rubric -> coverage ->
    technical checks -> scoring -> feedback.

    This is the single source of truth for evaluation logic — called by
    both the /practice/evaluate API route and the benchmark script,
    so both always use identical scoring behavior.
    """
    concepts = analyze_question(question_text, existing_concepts)
    rubric = build_rubric(concepts)

    concept_results = evaluate_concept_coverage(rubric, answer_text)
    technical_flags = check_technical_accuracy(answer_text, topic_name)

    scores = compute_scores(concept_results, technical_flags, answer_text)

    feedback = generate_feedback(
        concept_results=concept_results,
        technical_flags=technical_flags,
        dimension_scores=scores["dimension_scores"],
        overall_score=scores["overall_score"],
    )

    return {
        "evaluator_version": EVALUATOR_VERSION,
        "overall_score": scores["overall_score"],
        "dimension_scores": scores["dimension_scores"],
        "feedback": feedback,
        "rubric": rubric,
    }