# ml/scoring_engine.py


import re
def compute_scores(concept_results: list[dict], technical_flags: list[dict], answer_text: str) -> dict:
    completeness_score = _score_completeness(concept_results)
    correctness_score = _score_correctness(concept_results, technical_flags)
    clarity_score = _score_clarity(answer_text, concept_results)
    
    # GUARDRAIL: If 0 concepts are covered, force clarity score down and cap overall score
    total_covered = sum(1 for c in concept_results if c["status"] == "covered")
    if total_covered == 0:
        clarity_score = min(clarity_score, 40)

    overall_score = round(
        (completeness_score * 0.4) + (correctness_score * 0.4) + (clarity_score * 0.2)
    )

    if technical_flags or total_covered == 0:
        overall_score = min(overall_score, 15)

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
        covered_count = sum(1 for c in concept_results if c["status"] == "covered")
        partial_count = sum(1 for c in concept_results if c["status"] == "partial")
        matched_any = (covered_count + partial_count) > 0

        if matched_any:
            # High baseline if at least one concept is touched without false statements
            coverage_ratio = (covered_count + 0.5 * partial_count) / len(concept_results)
            base = round(70 + (coverage_ratio * 30))  # Scales from 70 to 100
        else:
            # Zero concept matches: Give a floor score of 50 if the answer is non-empty,
            # trusting that absence of detail is an completeness issue, not a hallucination.
            base = 50

    # Subtract heavy penalties ONLY for explicit technical errors/misconceptions
    penalty = len(technical_flags) * 20
    
    return max(0, base - penalty)




def _score_clarity(answer_text: str, concept_results: list[dict]) -> int:
    words = answer_text.strip().split()
    word_count = len(words)

    # 1. Reject empty or extreme low-effort answers immediately
    if word_count < 3:
        return 0

    # 2. Check for garbage / non-alphabetic input (e.g., "asdfasdf 1234 !!!")
    alpha_words = [w for w in words if re.search(r'[a-zA-Z]', w)]
    if len(alpha_words) / word_count < 0.5:
        return 0  # Mostly non-text / gibberish

    # 3. Base score according to length bands
    if word_count < 8:
        score = 30
    elif word_count < 20:
        score = 70
    elif word_count <= 200:
        score = 85
    else:
        score = 65  # Penalize heavy rambling

    # 4. Coherence Guardrail: If answer failed to cover ANY concepts, 
    # it cannot be considered "clear" technical communication.
    total_concepts = len(concept_results)
    covered_or_partial = sum(
        1 for c in concept_results if c["status"] in ("covered", "partial")
    )

    if total_concepts > 0 and covered_or_partial == 0:
        # Cap clarity at 10-15 if zero relevant concepts were addressed
        score = min(score, 15)

    return score