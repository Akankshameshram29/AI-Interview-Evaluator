import streamlit as st
from services.auth import require_login
from services.api_client import get_topics, get_questions

require_login()

st.title("Practice")

# --- Topic selection ---
topics = get_topics()
topic_names = [t["name"] for t in topics]
selected_name = st.selectbox("Select a topic", topic_names)
selected_topic = next(t for t in topics if t["name"] == selected_name)

st.caption(selected_topic["description"])

# --- Suggested questions ---
st.subheader("Suggested Questions")
questions = get_questions(selected_topic["id"])

selected_question_text = None

for q in questions:
    with st.container(border=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(q["question_text"])
            st.caption(f"Difficulty: {q['difficulty']}")
        with col2:
            if st.button("Use this", key=f"use_{q['id']}"):
                st.session_state["selected_question"] = q["question_text"]
                st.session_state["expected_concepts"] = q["expected_concepts"]
                st.session_state["question_source"] = "suggested"

# --- Custom question ---
st.subheader("Or write your own question")
custom_question = st.text_area(
    "Custom question",
    placeholder="Type any interview question you want to practice...",
)

if st.button("Use custom question"):
    if custom_question.strip():
        st.session_state["selected_question"] = custom_question.strip()
        st.session_state["expected_concepts"] = None  # will be derived Day 6
        st.session_state["question_source"] = "custom"
    else:
        st.warning("Please type a question first.")

# --- Show what's currently selected ---
st.divider()
if "selected_question" in st.session_state:
    st.success(f"Selected question: {st.session_state['selected_question']}")
    st.caption(f"Source: {st.session_state.get('question_source')}")
else:
    st.info("Pick a suggested question or write your own to continue.")