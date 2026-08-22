import json
import os
from ml.evaluation_service import run_evaluation
from ml.embedding_service import compute_similarity_matrix, split_into_sentences
from ml.question_analyzer import analyze_question
from ml.rubric_builder import build_rubric
import numpy as np

BENCHMARK_PATH = os.path.join(os.path.dirname(__file__), "labeled_qa_pairs.json")


def load_benchmark() -> list[dict]:
    with open(BENCHMARK_PATH, "r") as f:
        return json.load(f)


def run_all():
    examples = load_benchmark()

    total_tp, total_fp, total_fn = 0, 0, 0
    score_diffs = []

    print(f"{'Question':<50} {'Human':>6} {'Model':>6} {'Diff':>6}")
    print("-" * 72)

    for ex in examples:
        result = run_evaluation(
            question_text=ex["question"],
            answer_text=ex["answer"],
            topic_name=ex["topic"],
        )

        predicted_covered = {
            c["concept"] for c in result["feedback"]["concept_results"]
            if c["status"] == "covered"
        }
        actual_covered = set(ex["human_covered_concepts"])
        all_concepts = {c["concept"] for c in result["feedback"]["concept_results"]}

        tp = len(predicted_covered & actual_covered)
        fp = len(predicted_covered - actual_covered)
        fn = len(actual_covered - predicted_covered)

        total_tp += tp
        total_fp += fp
        total_fn += fn

        diff = result["overall_score"] - ex["human_score"]
        score_diffs.append(diff)

        print(f"{ex['question'][:47]:<50} {ex['human_score']:>6} {result['overall_score']:>6} {diff:>+6}")

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0

    avg_abs_diff = sum(abs(d) for d in score_diffs) / len(score_diffs)

    print("\n--- Concept Coverage Metrics ---")
    print(f"Precision: {precision:.3f}")
    print(f"Recall:    {recall:.3f}")
    print(f"F1:        {f1:.3f}")
    print(f"\n--- Overall Score Calibration ---")
    print(f"Average absolute difference from human score: {avg_abs_diff:.1f} points")





def sweep_thresholds():
    """
    Computes raw similarity scores for every concept in the benchmark,
    then tests a range of covered/partial thresholds to find the pair
    that maximizes F1 against human judgments.
    """
    examples = load_benchmark()

    all_scores = []  # list of (raw_score, is_actually_covered)

    for ex in examples:
        concepts = analyze_question(ex["question"], None)
        rubric = build_rubric(concepts)
        concept_names = [r["concept"] for r in rubric]
        sentences = split_into_sentences(ex["answer"])

        if not sentences or not concept_names:
            continue

        matrix = compute_similarity_matrix(concept_names, sentences)

        for i, concept in enumerate(concept_names):
            best_score = float(matrix[i].max())
            is_covered = concept in ex["human_covered_concepts"]
            all_scores.append((best_score, is_covered))

    print(f"\nCollected {len(all_scores)} concept-level data points for threshold sweep.\n")

    best_f1 = 0
    best_threshold = 0
    print(f"{'Threshold':>10} {'Precision':>10} {'Recall':>10} {'F1':>10}")
    for threshold in [round(t, 2) for t in np.arange(0.05, 0.45, 0.02)]:
        tp = sum(1 for score, covered in all_scores if score >= threshold and covered)
        fp = sum(1 for score, covered in all_scores if score >= threshold and not covered)
        fn = sum(1 for score, covered in all_scores if score < threshold and covered)

        precision = tp / (tp + fp) if (tp + fp) else 0
        recall = tp / (tp + fn) if (tp + fn) else 0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0

        print(f"{threshold:>10} {precision:>10.3f} {recall:>10.3f} {f1:>10.3f}")

        if f1 > best_f1:
            best_f1 = f1
            best_threshold = threshold

    print(f"\nBest single threshold by F1: {best_threshold} (F1={best_f1:.3f})")


if __name__ == "__main__":
    run_all()
    print("\n" + "=" * 72)
    sweep_thresholds()