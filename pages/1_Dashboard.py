import streamlit as st
from services.auth import require_login, get_token, logout

require_login()

st.title("Dashboard")
st.write(f"Logged in as: {st.session_state.get('user_email')}")
st.caption(f"Token (for debugging only): {get_token()[:20]}...")

if st.button("Logout"):
    logout()
    st.rerun()