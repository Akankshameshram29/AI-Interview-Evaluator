import streamlit as st
import pandas as pd
from components.sidebar import render_sidebar_identity
from services.auth import require_login
from services.api_client import get_progress, get_attempts

require_login()
render_sidebar_identity()

st.title("Progress & Analytics")
st.caption("Track your performance trends and target weak technical concepts.")

# Safe API fetch
try:
    progress_data = get_progress()
except Exception as e:
    st.error(f"Failed to load progress data: {e}")
    st.stop()

if not progress_data:
    st.info("No progress data yet. Complete a few practice attempts to see trends here!")
    st.stop()

df = pd.DataFrame(progress_data)

# Normalize backend column names (handles 'avg_score' vs 'average_score')
if "avg_score" in df.columns and "average_score" not in df.columns:
    df["average_score"] = df["avg_score"]

# Ensure numeric types
df["average_score"] = pd.to_numeric(df["average_score"], errors="coerce").fillna(0)
df["attempts_count"] = pd.to_numeric(df["attempts_count"], errors="coerce").fillna(0).astype(int)

# --- Topic Mastery with Dual-Encoding Accessibility ---
st.subheader("Topic Mastery")

for _, row in df.iterrows():
    topic_name = row["topic_name"]
    score = float(row["average_score"])
    attempts = int(row["attempts_count"])

    # Determine status label & indicator icon (Accessibility)
    if score >= 80:
        status, icon = "Strong Mastery", "🟢"
    elif score >= 60:
        status, icon = "Needs Practice", "🟡"
    else:
        status, icon = "Action Required", "🔴"

    with st.container(border=True):
        col_info, col_status = st.columns([3, 1])
        with col_info:
            st.markdown(f"**{topic_name}**")
            # Normalize progress value between 0.0 and 1.0
            norm_score = max(0.0, min(score / 100.0, 1.0))
            st.progress(norm_score, text=f"Average Score: {score:.1f}% ({attempts} attempts)")
        with col_status:
            st.write(f"**{icon} {status}**")

st.divider()

# --- Visualization & Breakdown Table ---
col_chart, col_table = st.columns([1, 1])

with col_chart:
    st.subheader("Performance Comparison")
    st.bar_chart(df.set_index("topic_name")["average_score"], use_container_width=True)

with col_table:
    st.subheader("Topic Breakdown")
    display_df = df[["topic_name", "average_score", "attempts_count"]].copy()
    display_df["average_score"] = display_df["average_score"].map(lambda val: f"{val:.1f}%")
    display_df.columns = ["Topic", "Avg Score", "Attempts"]
    st.dataframe(display_df, use_container_width=True, hide_index=True)

st.divider()

# --- Weak Concepts / Focus Areas ---
st.subheader("Concepts to Review")

weak_topics = df[df["average_score"] < 60]["topic_name"].tolist()

if weak_topics:
    st.warning("The following topics are below a 60% average. Consider focused practice here:")
    for topic in weak_topics:
        st.markdown(f"- **{topic}**")
else:
    st.success("No topics currently below 60% average — solid consistency across the board!")