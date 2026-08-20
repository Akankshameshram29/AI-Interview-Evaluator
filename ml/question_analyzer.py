import json
from groq import Groq
from config.settings import settings

groq_client = Groq(api_key=settings.GROQ_API_KEY)


def analyze_question(question_text: str, existing_concepts: list[str] | None = None) -> list[str]:
    """
    Returns a list of expected concept strings for a given interview question.
    If existing_concepts is provided (from a suggested question's DB row), use it directly.
    Otherwise, derive concepts using an LLM.
    """
    if existing_concepts:
        return existing_concepts

    prompt = f"""You are an expert technical interviewer. Given the interview question below,
list the key concepts a strong answer should cover.

Question: "{question_text}"

Return ONLY a JSON array of 3-6 short concept strings, nothing else.
Example format: ["gradient descent", "loss function", "learning rate"]"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=200,
        )
        raw_output = response.choices[0].message.content.strip()

        # Strip markdown code fences if the model wraps its output in them
        if raw_output.startswith("```"):
            raw_output = raw_output.strip("`")
            raw_output = raw_output.replace("json", "", 1).strip()

        concepts = json.loads(raw_output)
        if isinstance(concepts, list) and all(isinstance(c, str) for c in concepts):
            return concepts

    except Exception:
        pass

    # Fallback if LLM call or parsing fails — never leave the pipeline with nothing
    return _fallback_concepts(question_text)


def _fallback_concepts(question_text: str) -> list[str]:
    """Simple keyword-based fallback if the LLM call fails for any reason."""
    words = [w.strip(".,?!").lower() for w in question_text.split()]
    stopwords = {"what", "is", "the", "a", "an", "how", "does", "explain", "why", "of", "in", "and", "to"}
    keywords = [w for w in words if w not in stopwords and len(w) > 3]
    return keywords[:5] if keywords else ["general understanding"]