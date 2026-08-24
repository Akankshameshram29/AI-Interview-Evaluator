import streamlit as st
import pandas as pd
from services.auth import require_login
from services.api_client import get_attempts, get_attempt_detail

require_login()
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

# --- Attempt detail view ---
if "viewing_attempt_id" in st.session_state:
    st.divider()
    detail = get_attempt_detail(st.session_state["viewing_attempt_id"])

    st.subheader("Attempt Detail")
    st.write(f"**Topic:** {detail['topic_name']}")
    st.write(f"**Question:** {detail['question_text']}")
    st.write(f"**Answer:** {detail['answer_text']}")
    st.metric("Overall Score", f"{detail['overall_score']}/100" if detail['overall_score'] is not None else "—")

    if detail.get("dimension_scores"):
        cols = st.columns(len(detail["dimension_scores"]))
        for col, dim in zip(cols, detail["dimension_scores"]):
            with col:
                st.metric(dim["dimension"].capitalize(), f"{dim['score']}/100")

    if detail.get("feedback"):
        with st.expander("Full Feedback"):
            st.json(detail["feedback"])

    if st.button("Close Detail"):
        del st.session_state["viewing_attempt_id"]
        st.rerun()