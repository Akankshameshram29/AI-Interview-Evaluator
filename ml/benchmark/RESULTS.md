# Evaluator Calibration Results (Day 9)

Benchmark: 15 hand-labeled Q&A pairs across ML, DL, NLP, Python, SQL, GenAI.

## Concept Coverage (TF-IDF cosine similarity)
- Final threshold: COVERED=0.09, PARTIAL=0.05
- Precision/Recall/F1 varied across calibration runs (F1 range: 0.16-0.47)
  due to benchmark size (~84 concept data points) being too small for
  fully stable threshold selection — final values chosen based on the
  threshold most frequently recommended by repeated sweeps.

## Known limitation
TF-IDF cosine similarity favors recall over precision — it reliably
flags genuinely covered concepts but sometimes over-credits partial
matches. A semantic embedding approach (e.g. sentence-transformers)
would likely improve precision, but was avoided due to native library
(PyTorch/CTranslate2) crashes encountered on the development machine.
A hosted embeddings API is a reasonable V2 upgrade.

## Scoring adjustments made
- Overall score capped at 35 when technical misconceptions are detected,
  regardless of clarity/completeness, to avoid misleadingly moderate
  scores on factually incorrect answers.
- Clarity scoring bands widened to avoid penalizing concise-but-correct
  answers.