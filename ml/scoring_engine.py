# ml/scoring_engine.py

def compute_scores(concept_results: list[dict], technical_flags: list[dict], answer_text: str) -> dict:
    completeness_score = _score_completeness(concept_results)
    correctness_score = _score_correctness(concept_results, technical_flags)
    clarity_score = _score_clarity(answer_text)

    overall_score = round(
        (completeness_score * 0.4) + (correctness_score * 0.4) + (clarity_score * 0.2)
    )

    # If technical flags were raised, cap the overall score regardless of clarity —
    # a technically wrong answer shouldn't score moderately well just because it's concise
    if technical_flags:
        overall_score = min(overall_score, 35)

    return {
        "overall_score": overall_score,
        "dimension_scores": [
            {"dimension": "correctness", "score": correctness_score},
            {"dimension": "completeness", "score": completeness_score},
            {"dimension": "clarity", "score": clarity_score},
        ],
    }


def _score_completeness(concept_results: list[dict]) -> int:
    """
    Weighted average of concept coverage — covered = full weight,
    partial = half weight, missing = zero.
    """
    if not concept_results:
        return 0

    total_weight = sum(c["weight"] for c in concept_results)
    if total_weight == 0:
        return 0

    earned = 0
    for c in concept_results:
        if c["status"] == "covered":
            earned += c["weight"]
        elif c["status"] == "partial":
            earned += c["weight"] * 0.5
        # missing contributes 0

    return round((earned / total_weight) * 100)


def _score_correctness(concept_results: list[dict], technical_flags: list[dict]) -> int:
    """
    Starts from a baseline tied to how well the answer aligns with
    expected concepts (a wildly off-topic answer isn't "correct" either),
    then subtracts a penalty for each technical flag raised.
    """
    if not concept_results:
        base = 50  # no rubric to compare against — neutral baseline
    else:
        # Use the same coverage-based signal as completeness as a starting point,
        # since an answer that doesn't touch the right concepts at all
        # can't be scored as "correct" independent of what it does say
        covered_or_partial = sum(
            1 for c in concept_results if c["status"] in ("covered", "partial")
        )
        base = round((covered_or_partial / len(concept_results)) * 100)

    penalty = min(len(technical_flags) * 20, base)  # never go below 0
    return max(0, base - penalty)


def _score_clarity(answer_text: str) -> int:
    """
    Simple heuristic clarity score based on length and structure —
    not a deep NLP measure, just enough to avoid a flat constant.
    Very short or very rambling answers score lower.

    Bands adjusted (Day 9 calibration) after benchmark testing showed
    concise-but-complete answers (e.g. short, precise technical
    definitions) were being penalized too harshly under the original
    <40-word band.
    """
    word_count = len(answer_text.split())

    if word_count < 8:
        return 40
    elif word_count < 20:
        return 70
    elif word_count <= 200:
        return 85
    else:
        return 70