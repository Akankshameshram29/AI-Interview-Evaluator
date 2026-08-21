# ml/technical_checker.py

# Each entry: if the answer contains the "wrong_phrase" in a context
# suggesting it as fact, flag it. This is intentionally simple —
# a small, curated set of common interview misconceptions per topic.
KNOWN_MISCONCEPTIONS = {
    "ML": [
        {
            "wrong_phrase": "high bias and high variance always occur together",
            "flag": "Bias and variance are typically a tradeoff, not something that always increases together.",
        },
        {
            "wrong_phrase": "more data always reduces bias",
            "flag": "More data primarily helps reduce variance, not bias — a biased model stays biased regardless of data volume.",
        },
    ],
    "DL": [
        {
            "wrong_phrase": "relu solves vanishing gradients completely",
            "flag": "ReLU helps mitigate vanishing gradients but doesn't eliminate the problem completely (e.g. dying ReLU, deep networks can still suffer).",
        },
    ],
    "SQL": [
        {
            "wrong_phrase": "inner join returns all rows from both tables",
            "flag": "INNER JOIN only returns rows with matches in both tables — that description matches FULL OUTER JOIN instead.",
        },
    ],
    "Python": [
        {
            "wrong_phrase": "lists are immutable",
            "flag": "Lists in Python are mutable — this describes tuples instead.",
        },
    ],
    "NLP": [],
    "GenAI": [],
}


def check_technical_accuracy(answer_text: str, topic_name: str) -> list[dict]:
    """
    Runs simple keyword/phrase-based checks against known misconceptions
    for the given topic. Returns a list of flags, each with the
    problematic phrase and an explanation.
    """
    answer_lower = answer_text.lower()
    misconceptions = KNOWN_MISCONCEPTIONS.get(topic_name, [])

    flags = []
    for item in misconceptions:
        if item["wrong_phrase"] in answer_lower:
            flags.append({
                "issue": item["wrong_phrase"],
                "explanation": item["flag"],
            })

    return flags