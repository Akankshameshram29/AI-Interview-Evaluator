from ml.rubric_builder import build_rubric


def test_rubric_weights_sum_to_100():
    concepts = ["a", "b", "c"]
    rubric = build_rubric(concepts)
    total_weight = sum(item["weight"] for item in rubric)
    assert total_weight == 100


def test_rubric_empty_concepts_returns_empty_list():
    assert build_rubric([]) == []


def test_rubric_single_concept_gets_full_weight():
    rubric = build_rubric(["only_one"])
    assert rubric[0]["weight"] == 100