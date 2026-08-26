import streamlit as st
import pandas as pd
from components.sidebar import render_sidebar_identity
from services.auth import require_login
from services.api_client import get_attempts, get_attempt_detail

require_login()
render_sidebar_identity()
st.title("History")

attempts = get_attempts()

if not attempts:
    st.info("No practice attempts yet. Head to Practice to get started.")
    st.stop()

df = pd.DataFrame(attempts)
df["created_at"] = pd.to_datetime(df["created_at"])

# --- Filters ---
col1, col2, col3 = st.columns(3)
with col1:
    topic_filter = st.selectbox("Filter by topic", ["All"] + sorted(df["topic_name"].unique().tolist()))
with col2:
    mode_filter = st.selectbox("Filter by mode", ["All", "text", "voice"])
with col3:
    sort_by = st.selectbox("Sort by", ["Newest first", "Oldest first", "Highest score", "Lowest score"])

filtered = df.copy()
if topic_filter != "All":
    filtered = filtered[filtered["topic_name"] == topic_filter]
if mode_filter != "All":
    filtered = filtered[filtered["answer_mode"] == mode_filter]

if sort_by == "Newest first":
    filtered = filtered.sort_values("created_at", ascending=False)
elif sort_by == "Oldest first":
    filtered = filtered.sort_values("created_at", ascending=True)
elif sort_by == "Highest score":
    filtered = filtered.sort_values("overall_score", ascending=False)
elif sort_by == "Lowest score":
    filtered = filtered.sort_values("overall_score", ascending=True)

st.write(f"Showing {len(filtered)} of {len(df)} attempts")

# --- List as cards, each openable ---
for _, row in filtered.iterrows():
    with st.container(border=True):
        col_a, col_b, col_c = st.columns([3, 1, 1])
        with col_a:
            st.write(f"**{row['question_text'][:80]}**")
            st.caption(f"{row['topic_name']} · {row['answer_mode'].capitalize()} · {row['source'].capitalize()}")
        with col_b:
            score_display = f"{row['overall_score']}/100" if row['overall_score'] is not None else "—"
            st.metric("Score", score_display)
        with col_c:
            st.caption(row["created_at"].strftime("%b %d, %Y"))

        if st.button("View Details", key=f"view_{row['attempt_id']}"):
            st.session_state["viewing_attempt_id"] = row["attempt_id"]
            st.rerun()

from components.evaluation_display import render_evaluation_result

# --- Render Attempt Detail Section ---
if "viewing_attempt_id" in st.session_state:
    st.divider()
    
    col_title, col_close = st.columns([5, 1])
    with col_title:
        st.subheader("Attempt Details")
    with col_close:
        if st.button("✖️ Close"):
            st.session_state.pop("viewing_attempt_id", None)
            st.rerun()

    # Fetch full attempt data using the saved attempt_id
    attempt_id = st.session_state["viewing_attempt_id"]
    with st.spinner("Loading attempt details..."):
        try:
            detail = get_attempt_detail(attempt_id)
            render_evaluation_result(
                overall_score=detail["overall_score"],
                dimension_scores=detail["dimension_scores"],
                feedback=detail["feedback"],
                question_text=detail["question_text"],
                answer_text=detail["answer_text"],
                answer_mode=detail["answer_mode"],
            )
        except Exception as e:
            st.error(f"Failed to load attempt details: {e}")