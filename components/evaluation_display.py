# components/evaluation_display.py
import streamlit as st

def render_evaluation_result(overall_score: int, dimension_scores: list[dict], feedback: dict, question_text: str, answer_text: str, answer_mode: str):
    """
    Renders a full evaluation result in the standard order:
    overall -> dimensions -> concept coverage -> strengths/corrections -> improvements -> original Q&A.
    Shared between the Practice page (right after evaluating) and the
    History page (viewing a past attempt's detail).
    """
    st.metric("Overall Score", f"{overall_score} / 100")

    st.write("**Dimension Scores**")
    cols = st.columns(len(dimension_scores))
    for col, dim in zip(cols, dimension_scores):
        with col:
            st.metric(dim["dimension"].capitalize(), f"{dim['score']} / 100")

    st.write("**Concept Coverage**")
    concept_results = feedback.get("concept_results", [])
    if not concept_results:
        st.info("No concept analysis available for this answer.")
    else:
        status_icon = {"covered": "✅", "partial": "🟡", "missing": "❌"}
        for concept in concept_results:
            icon = status_icon.get(concept["status"], "")
            st.write(f"{icon} **{concept['concept']}** — {concept['status'].capitalize()}")
            if concept.get("evidence"):
                st.caption(f"Evidence: \"{concept['evidence']}\"")

    with st.expander("Strengths", expanded=True):
        for s in feedback.get("strengths", []):
            st.write(f"- {s}")

    if feedback.get("technical_flags"):
        with st.expander("Corrections", expanded=True):
            for flag in feedback["technical_flags"]:
                st.write(f"⚠️ {flag['explanation']}")

    with st.expander("Improvement Plan"):
        for imp in feedback.get("improvements", []):
            st.write(f"- {imp}")

    with st.expander("Original Question & Answer"):
        st.write(f"**Question:** {question_text}")
        st.write(f"**Answer:** {answer_text}")
        st.caption(f"Mode: {answer_mode.capitalize()}")