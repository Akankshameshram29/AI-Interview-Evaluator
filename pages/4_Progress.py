import streamlit as st
import pandas as pd
from services.auth import require_login
from services.api_client import get_progress, get_attempts

require_login()
st.title("Progress")

progress_data = get_progress()

if not progress_data:
    st.info("No progress data yet. Complete a few practice attempts to see trends here.")
    st.stop()

df = pd.DataFrame(progress_data)

# --- Overview: average score per topic ---
st.subheader("Average Score by Topic")
st.bar_chart(df.set_index("topic_name")["average_score"])

# --- Table view ---
st.subheader("Topic Breakdown")
display_df = df[["topic_name", "average_score", "attempts_count"]].rename(columns={
    "topic_name": "Topic",
    "average_score": "Average Score",
    "attempts_count": "Attempts",
})
st.dataframe(display_df, use_container_width=True, hide_index=True)

# --- Weak concepts: derive from recent attempts' concept_results ---
st.subheader("Concepts to Review")
attempts = get_attempts()
weak_topics = df[df["average_score"] < 60]["topic_name"].tolist()

if weak_topics:
    st.write("Topics below 60% average — consider more practice here:")
    for topic in weak_topics:
        st.write(f"- **{topic}**")
else:
    st.success("No topics currently below 60% average — good progress across the board.")