from ml.scoring_engine import compute_scores, _score_completeness, _score_correctness, _score_clarity


def test_completeness_all_covered():
    concept_results = [
        {"concept": "a", "weight": 50, "status": "covered"},
        {"concept": "b", "weight": 50, "status": "covered"},
    ]
    assert _score_completeness(concept_results) == 100


def test_completeness_all_missing():
    concept_results = [
        {"concept": "a", "weight": 50, "status": "missing"},
        {"concept": "b", "weight": 50, "status": "missing"},
    ]
    assert _score_completeness(concept_results) == 0


def test_completeness_partial_gets_half_credit():
    concept_results = [{"concept": "a", "weight": 100, "status": "partial"}]
    assert _score_completeness(concept_results) == 50


def test_completeness_empty_list_returns_zero():
    assert _score_completeness([]) == 0


def test_correctness_penalized_by_technical_flags():
    concept_results = [{"concept": "a", "weight": 100, "status": "covered"}]
    no_flags_score = _score_correctness(concept_results, [])
    with_flag_score = _score_correctness(concept_results, [{"issue": "x", "explanation": "y"}])
    assert with_flag_score < no_flags_score


def test_correctness_never_goes_below_zero():
    concept_results = [{"concept": "a", "weight": 100, "status": "missing"}]
    many_flags = [{"issue": f"x{i}", "explanation": "y"} for i in range(10)]
    assert _score_correctness(concept_results, many_flags) == 0


def test_clarity_very_short_answer_scores_low():
    assert _score_clarity("too short") == 40


def test_clarity_reasonable_answer_scores_higher():
    long_answer = " ".join(["word"] * 50)
    assert _score_clarity(long_answer) == 85


def test_compute_scores_caps_when_technical_flags_present():
    concept_results = [{"concept": "a", "weight": 100, "status": "covered"}]
    technical_flags = [{"issue": "x", "explanation": "y"}]
    result = compute_scores(concept_results, technical_flags, "a reasonably long correct-sounding answer here")
    assert result["overall_score"] <= 35