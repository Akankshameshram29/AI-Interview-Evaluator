import streamlit as st
from services.api_client import login, register
from services.auth import save_token, is_authenticated

st.set_page_config(page_title="AI Interview Evaluator", page_icon="🎤")

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
        submitted = st.form_submit_button("Login")

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
        reg_submitted = st.form_submit_button("Register")

    if reg_submitted:
        try:
            result = register(reg_email, reg_password, reg_name)
            save_token(result["access_token"], reg_email)
            st.success("Account created! Reloading...")
            st.rerun()
        except Exception as e:
            st.error("Registration failed — email may already be in use.")