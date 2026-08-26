import streamlit as st
import requests
from services.api_client import login, register
from services.auth import save_token, is_authenticated


st.set_page_config(page_title="AI Interview Evaluator", page_icon="🎤", layout="centered")

# 2. Custom CSS Block
st.markdown("""
<style>
    /* Metric styling */
    div[data-testid="stMetric"] {
        background-color: rgba(28, 131, 225, 0.05);
        border-radius: 8px;
        padding: 12px;
    }
    
    /* Center and elevate login container */
    .stForm {
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        padding: 24px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    /* Make submit buttons full width */
    div[data-testid="stFormSubmitButton"] > button {
        width: 100%;
        border-radius: 6px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# 3. Authentication Check
if is_authenticated():
    st.success("You're already logged in.")
    st.write("Use the sidebar to navigate to Dashboard.")
    st.stop()

st.title("AI Interview Answer Evaluator")

tab_login, tab_register = st.tabs(["Login", "Register"])

with tab_login:
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", use_container_width=True)

    if submitted:
        try:
            result = login(email, password)
            save_token(result["access_token"], email)
            st.success("Logged in! Reloading...")
            st.rerun()
        except Exception as e:
            st.error("Invalid email or password.")

with tab_register:
    with st.form("register_form"):
        reg_name = st.text_input("Name")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_submitted = st.form_submit_button("Register", use_container_width=True)

    if reg_submitted:
        try:
            result = register(reg_email, reg_password, reg_name)
            save_token(result["access_token"], reg_email)
            st.success("Account created! Reloading...")
            st.rerun()
        except requests.exceptions.HTTPError as e:
            try:
                detail = e.response.json().get("detail", "Unknown error")
            except Exception:
                detail = e.response.text
            st.error(f"Registration failed: {detail}")
        except Exception as e:
            st.error(f"Unexpected error: {type(e).__name__}: {e}")