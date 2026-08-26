import streamlit as st
from services.auth import require_login
from services.api_client import get_attempts, get_progress
from components.sidebar import render_sidebar_identity

require_login()
render_sidebar_identity()

st.title("Dashboard")

attempts = get_attempts()
progress = get_progress()

# --- Top-level metrics in columns ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Attempts", len(attempts))
with col2:
    avg_score = round(sum(a["overall_score"] for a in attempts if a["overall_score"] is not None) / len(attempts)) if attempts else 0
    st.metric("Average Score", f"{avg_score}/100" if attempts else "—")
with col3:
    st.metric("Topics Practiced", len(progress))

st.divider()

# --- Recent attempts ---
st.subheader("Recent Attempts")
if not attempts:
    st.info("No attempts yet — head to Practice to get started.")
else:
    for a in attempts[:5]:
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.write(f"**{a['question_text'][:70]}**")
                st.caption(f"{a['topic_name']} · {a['answer_mode'].capitalize()}")
            with c2:
                score = f"{a['overall_score']}/100" if a['overall_score'] is not None else "—"
                st.metric("Score", score)

st.divider()

if st.button("Start Practice", type="primary", use_container_width=True):
    st.switch_page("pages/2_Practice.py")