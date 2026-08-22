# ml/feedback_generator.py

def generate_feedback(
    concept_results: list[dict],
    technical_flags: list[dict],
    dimension_scores: list[dict],
    overall_score: int,
) -> dict:
    """
    Turns scoring output into structured, explainable feedback:
    strengths, gaps, and concrete improvement suggestions.
    """
    covered = [c for c in concept_results if c["status"] == "covered"]
    partial = [c for c in concept_results if c["status"] == "partial"]
    missing = [c for c in concept_results if c["status"] == "missing"]

    strengths = _build_strengths(covered, dimension_scores)
    gaps = _build_gaps(partial, missing)
    improvements = _build_improvements(missing, partial, technical_flags, overall_score)

    return {
        "strengths": strengths,
        "gaps": gaps,
        "improvements": improvements,
        "concept_results": concept_results,
        "technical_flags": technical_flags,
    }


def _build_strengths(covered: list[dict], dimension_scores: list[dict]) -> list[str]:
    strengths = []

    if covered:
        concept_names = ", ".join(c["concept"] for c in covered)
        strengths.append(f"Clearly addressed: {concept_names}.")

    clarity = next((d["score"] for d in dimension_scores if d["dimension"] == "clarity"), None)
    if clarity is not None and clarity >= 80:
        strengths.append("The answer is well-structured and appropriately detailed.")

    if not strengths:
        strengths.append("Answer submitted and evaluated.")

    return strengths


def _build_gaps(partial: list[dict], missing: list[dict]) -> list[str]:
    gaps = []

    if partial:
        names = ", ".join(c["concept"] for c in partial)
        gaps.append(f"Touched on but under-explained: {names}.")

    if missing:
        names = ", ".join(c["concept"] for c in missing)
        gaps.append(f"Not addressed: {names}.")

    if not gaps:
        gaps.append("No significant concept gaps detected.")

    return gaps


def _build_improvements(
    missing: list[dict],
    partial: list[dict],
    technical_flags: list[dict],
    overall_score: int,
) -> list[str]:
    improvements = []

    for flag in technical_flags:
        improvements.append(flag["explanation"])

    if missing:
        top_missing = ", ".join(c["concept"] for c in missing[:3])
        improvements.append(f"Add explanation of: {top_missing}.")

    if partial:
        top_partial = ", ".join(c["concept"] for c in partial[:2])
        improvements.append(f"Go deeper on: {top_partial} — mentioned but not fully explained.")

    if overall_score >= 85 and not improvements:
        improvements.append("Strong answer — consider adding a concrete example to make it even clearer.")
    elif not improvements:
        improvements.append("Consider adding more depth or examples.")

    return improvements