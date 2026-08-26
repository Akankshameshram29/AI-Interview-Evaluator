import streamlit as st


def _get_score_color(score: float | int) -> str:
    """Returns a CSS color based on the score threshold."""
    if score >= 80:
        return "#10B981"  # Emerald Green
    elif score >= 60:
        return "#F59E0B"  # Amber/Yellow
    return "#EF4444"      # Red


def render_evaluation_result(
    overall_score: float | int,
    dimension_scores: dict,
    feedback: dict,
    question_text: str = "",
    answer_text: str = "",
    answer_mode: str = "text",
):
    """Renders a polished, multi-tab evaluation report card."""

    # --- Header Score Card ---
    label, color, icon = _get_score_metadata(overall_score)
    st.markdown(
        f"""
        <div style="
            background-color: rgba(28, 131, 225, 0.05);
            border-left: 6px solid {color};
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 20px;
        ">
            <h3 style="margin: 0; padding: 0;">Overall Performance</h3>
            <p style="font-size: 32px; font-weight: 700; color: {color}; margin: 4px 0 0 0;">
                {overall_score} <span style="font-size: 18px; color: #666;">/ 100</span>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Dimensional Scores Grid ---
    st.subheader("Performance Dimensions")
    if dimension_scores:
        cols = st.columns(len(dimension_scores))
        for idx, (dim, score) in enumerate(dimension_scores.items()):
            dim_label, _, dim_icon = _get_score_metadata(score)
            with cols[idx]:
                st.metric(
                    label=dim.replace("_", " ").title(),
                    value=f"{score}%",
                    delta=f"{dim_icon} {dim_label}",
                    delta_color="off",  # Color override turned off for custom text clarity
                )

    st.divider()

    # --- Detailed Feedback Tabs ---
    tab_feedback, tab_concepts, tab_submission = st.tabs(
        ["💡 Detailed Feedback", "🎯 Concept Coverage", "📝 Original Submission"]
    )

    # TAB 1: Detailed Feedback (Strengths, Improvements, Sample Answer)
    with tab_feedback:
        col_strengths, col_improvements = st.columns(2)

        with col_strengths:
            st.markdown("#### ✅ Strengths")
            strengths = feedback.get("strengths", [])
            if strengths:
                for item in strengths:
                    st.success(f"• {item}")
            else:
                st.caption("No specific strengths listed.")

        with col_improvements:
            st.markdown("#### 🎯 Areas to Improve")
            improvements = feedback.get("improvements", [])
            if improvements:
                for item in improvements:
                    st.warning(f"• {item}")
            else:
                st.caption("No key improvements needed!")

        if feedback.get("sample_answer"):
            st.markdown("---")
            st.markdown("#### 🌟 Model Answer Concept")
            st.info(feedback["sample_answer"])

    # TAB 2: Concept Badges
    with tab_concepts:
        st.markdown("#### Key Technical Concepts")

        covered = feedback.get("concepts_covered", [])
        missed = feedback.get("concepts_missed", [])

        if covered:
            st.write("**Covered in your answer:**")
            badge_html = " ".join([
                f'<span style="background-color: #D1FAE5; color: #065F46; padding: 4px 10px; border-radius: 12px; font-weight: 500; font-size: 14px; margin-right: 6px; display: inline-block;">✓ {c}</span>'
                for c in covered
            ])
            st.markdown(badge_html, unsafe_allow_html=True)
            st.write("")

        if missed:
            st.write("**Missed concepts:**")
            badge_html = " ".join([
                f'<span style="background-color: #FEE2E2; color: #991B1B; padding: 4px 10px; border-radius: 12px; font-weight: 500; font-size: 14px; margin-right: 6px; display: inline-block;">✗ {c}</span>'
                for c in missed
            ])
            st.markdown(badge_html, unsafe_allow_html=True)

        if not covered and not missed:
            st.caption("No concept tagging available for this question.")

    # TAB 3: Original Question and Submitted Answer
    with tab_submission:
        if question_text:
            st.markdown("**Question:**")
            st.write(f"> {question_text}")

        if answer_text:
            st.markdown(f"**Your Answer ({answer_mode.upper()}):**")
            st.text_area("Answer text", value=answer_text, height=150, disabled=True)