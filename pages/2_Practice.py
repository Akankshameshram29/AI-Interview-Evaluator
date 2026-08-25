import streamlit as st
from services.auth import require_login
from services.api_client import get_topics, get_questions
from services.api_client import submit_evaluation, transcribe_audio


require_login()

st.title("Practice")

def on_topic_change():
    """Clears answers, transcripts, and prior evaluations when topic changes."""
    for key in [
        "selected_question",
        "expected_concepts",
        "question_source",
        "transcription_id",
        "transcript_text",
        "last_audio_id",
        "last_evaluation",
    ]:
        st.session_state.pop(key, None)

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
                st.session_state.pop("last_evaluation", None)

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
        st.session_state.pop("last_evaluation", None)
    else:
        st.warning("Please type a question first.")

# --- Show what's currently selected ---
st.divider()
if "selected_question" in st.session_state:
    st.success(f"Selected question: {st.session_state['selected_question']}")
    st.caption(f"Source: {st.session_state.get('question_source')}")
else:
    st.info("Pick a suggested question or write your own to continue.")



st.divider()

if "selected_question" in st.session_state:
    st.subheader("Your Answer")

    answer_mode = st.radio(
        "Answer mode",
        options=["Text", "Voice"],
        horizontal=True,
        key="answer_mode_selection",
    )

    if answer_mode == "Voice":
        st.caption("Recording will be capped at 5 minutes.")

        audio_value = st.audio_input("Record your answer")

        if audio_value is not None:
            if st.session_state.get("last_audio_id") != id(audio_value):
                with st.spinner("Transcribing your answer..."):
                    try:
                        audio_bytes = audio_value.read()
                        result = transcribe_audio(audio_bytes)

                        # Check if API returned an error string or empty transcript
                        if isinstance(result, dict) and result.get("transcript", "").strip():
                            st.session_state["transcription_id"] = result["transcription_id"]
                            st.session_state["transcript_text"] = result["transcript"]
                            st.session_state["last_audio_id"] = id(audio_value)
                        else:
                            st.warning("⚠️ No clear speech detected in your recording. Please try speaking into your mic again.")
                            for key in ["transcription_id", "transcript_text", "last_audio_id"]:
                                st.session_state.pop(key, None)

                    except Exception as e:
                        # Display clear error message when FastAPI throws a 422 (silence) or 400
                        err_msg = str(e)
                        if "422" in err_msg or "No speech detected" in err_msg:
                            st.warning("⚠️ No clear speech detected in your recording. Please check your mic and try again.")
                        else:
                            st.error(f"Transcription failed: {err_msg}")
                        
                        for key in ["transcription_id", "transcript_text", "last_audio_id"]:
                            st.session_state.pop(key, None)

        if "transcript_text" in st.session_state:
            st.success("Transcription complete. Review and edit below if needed.")
            edited_transcript = st.text_area(
                "Transcript (editable)",
                value=st.session_state["transcript_text"],
                height=200,
                key="transcript_editor",
            )
            st.session_state["transcript_text"] = edited_transcript

            if st.button("Re-record"):
                for key in ["transcription_id", "transcript_text", "last_audio_id"]:
                    st.session_state.pop(key, None)
                st.rerun()

        answer_text = st.session_state.get("transcript_text", "")

    else:
        answer_text = st.text_area("Type your answer here", height=200, key="answer_text_input")
        # Clear any leftover voice state when switching back to Text
        for key in ["transcription_id", "transcript_text", "last_audio_id"]:
            st.session_state.pop(key, None)

    evaluate_clicked = st.button(
        "Evaluate Answer",
        disabled=not answer_text.strip(),
    )

    if evaluate_clicked:
        with st.spinner("Evaluating your answer..."):
            result = submit_evaluation(
                topic_id=selected_topic["id"],
                question_text=st.session_state["selected_question"],
                answer_text=answer_text.strip(),
                answer_mode="voice" if answer_mode == "Voice" else "text",
                source=st.session_state.get("question_source", "custom"),
                transcription_id=st.session_state.get("transcription_id"),
            )
        st.session_state["last_evaluation"] = result
        st.success("Evaluation complete!")
        # Clear temporary voice/text state now that the attempt is finalized
        for key in ["transcription_id", "transcript_text", "last_audio_id"]:
            st.session_state.pop(key, None)

from components.evaluation_display import render_evaluation_result

if "last_evaluation" in st.session_state:
    result = st.session_state["last_evaluation"]
    st.divider()
    st.subheader("Results")
    render_evaluation_result(
        overall_score=result["overall_score"],
        dimension_scores=result["dimension_scores"],
        feedback=result["feedback"],
        question_text=result["question_text"],
        answer_text=result["answer_text"],
        answer_mode=result["answer_mode"],
    )