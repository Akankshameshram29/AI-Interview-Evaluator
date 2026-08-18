import streamlit as st
import requests

st.title("AI Interview Answer Evaluator — Setup Check")

if st.button("Ping Backend"):
    try:
        response = requests.get("http://localhost:8000/hello")
        data = response.json()
        st.success(f"{data['message']} | DB time: {data['db_time']}")
    except Exception as e:
        st.error(f"Backend not reachable: {e}")