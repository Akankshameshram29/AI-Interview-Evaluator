import streamlit as st

def save_token(token: str, email: str):
    st.session_state["access_token"] = token
    st.session_state["user_email"] = email

def get_token() -> str | None:
    return st.session_state.get("access_token")

def is_authenticated() -> bool:
    return "access_token" in st.session_state

def logout():
    st.session_state.pop("access_token", None)
    st.session_state.pop("user_email", None)

def require_login():
    """Call this at the top of every protected page."""
    if not is_authenticated():
        st.warning("Please log in to continue.")
        st.stop()