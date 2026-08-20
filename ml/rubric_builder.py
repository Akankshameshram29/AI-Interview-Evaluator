def build_rubric(concepts: list[str]) -> list[dict]:
    """
    Converts a flat list of expected concepts into a weighted rubric.
    Each concept gets an equal weight by default, normalized to sum to 100.
    """
    if not concepts:
        return []

    concept_count = len(concepts)
    base_weight = round(100 / concept_count)

    rubric = []
    running_total = 0
    for i, concept in enumerate(concepts):
        # Give the last concept whatever weight remains, so the total is always exactly 100
        if i == concept_count - 1:
            weight = 100 - running_total
        else:
            weight = base_weight
            running_total += weight

        rubric.append({
            "concept": concept,
            "weight": weight,
        })

    return rubric