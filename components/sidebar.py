# components/render_sidebar_identity.py
import streamlit as st
from services.auth import logout

def render_sidebar_identity():
    """Shows the logged-in user's identity and a logout button in the sidebar.
    Call this at the top of every protected page, after require_login()."""
    with st.sidebar:
        st.title("🎤 AI Evaluator")
        st.caption("Interview Prep Companion")
        st.divider()
        user_email = st.session_state.get("user_email", "User")
        st.markdown("**Active Account:**")
        st.info(f"👤 {user_email}", icon="🔒")

        st.divider()

        # Quick session action
        if st.button("Log Out", key="sidebar_logout_btn", use_container_width=True, help="End your active session"):
            logout()
            st.rerun()