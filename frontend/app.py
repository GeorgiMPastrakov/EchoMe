import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.title("EchoMe - Signup & Login Demo")

action = st.sidebar.selectbox("Select Action", ["Signup", "Login"])

if action == "Signup":
    st.header("Signup")
    username = st.text_input("Enter username", key="signup_username")
    password = st.text_input("Enter password", type="password", key="signup_password")
    
    if st.button("Signup"):
        payload = {"username": username, "password": password}
        response = requests.post(f"{API_URL}/signup", json=payload)
        if response.status_code == 200:
            st.success("Signup successful!")
            st.write("User Info:", response.json())
        else:
            error_detail = response.json().get("detail", "An error occurred")
            st.error(f"Signup failed: {error_detail}")

elif action == "Login":
    st.header("Login")
    username = st.text_input("Enter username", key="login_username")
    password = st.text_input("Enter password", type="password", key="login_password")
    
    if st.button("Login"):
        payload = {"username": username, "password": password}
        response = requests.post(f"{API_URL}/login", json=payload)
        if response.status_code == 200:
            st.success("Login successful!")
            st.write("User Info:", response.json())
        else:
            error_detail = response.json().get("detail", "An error occurred")
            st.error(f"Login failed: {error_detail}")

    uploaded_file = st.file_uploader("Upload audio (WAV)", type=["wav"])

if uploaded_file:
    files = {"audio_file": uploaded_file.getvalue()}
    data = {"user_id": user_id, "voice_name": "MyVoice"}
    response = requests.post(f"{API_URL}/upload_audio", files=files, data=data)

    if response.status_code == 200:
        st.success("Audio uploaded and saved!")
    else:
        st.error("Upload failed")