import streamlit as st
import requests
import os
from io import BytesIO
import base64
import soundfile as sf
import sounddevice as sd

API_URL = "http://localhost:8000"

st.set_page_config(page_title="EchoMe", layout="wide")
st.title("EchoMe - AI Voice Cloning Platform")

page = st.sidebar.radio("Navigate", ["Home", "Signup", "Login", "Dashboard"])

if page == "Home":
    st.header("Welcome to EchoMe")
    st.write("An AI voice cloning platform. Please sign up or log in to get started.")

elif page == "Signup":
    st.header("Sign Up")
    signup_username = st.text_input("Username", key="signup_username")
    signup_password = st.text_input("Password", type="password", key="signup_password")
    if st.button("Sign Up"):
        payload = {"username": signup_username, "password": signup_password}
        res = requests.post(f"{API_URL}/signup", json=payload)
        if res.status_code == 200:
            st.success("Signup successful! Please log in.")
        else:
            st.error(res.json().get("detail", "Signup failed."))

elif page == "Login":
    st.header("Log In")
    login_username = st.text_input("Username", key="login_username")
    login_password = st.text_input("Password", type="password", key="login_password")
    if st.button("Log In"):
        payload = {"username": login_username, "password": login_password}
        res = requests.post(f"{API_URL}/login", json=payload)
        if res.status_code == 200:
            st.session_state.user = res.json()
            st.success("Login successful!")
        else:
            st.error(res.json().get("detail", "Login failed."))

elif page == "Dashboard":
    if "user" not in st.session_state:
        st.error("Please log in first.")
    else:
        user = st.session_state.user
        st.header(f"Dashboard - Welcome, {user['username']}")

        tab = st.radio("Choose Action", ["Upload Audio", "Record Voice", "Generate AI Voice"])

        if tab == "Upload Audio":
            st.subheader("Upload an Audio File")
            uploaded_file = st.file_uploader("Choose a WAV file", type=["wav"])
            if uploaded_file is not None:
                if st.button("Upload"):
                    files = {"audio_file": uploaded_file.getvalue()}
                    file_payload = {
                        "audio_file": (uploaded_file.name, uploaded_file.getvalue(), "audio/wav")
                    }
                    data_payload = {"user_id": user["id"], "voice_name": "Uploaded Voice"}
                    res = requests.post(f"{API_URL}/upload_audio", files=file_payload, data=data_payload)
                    if res.status_code == 200:
                        st.success("Audio uploaded successfully!")
                    else:
                        st.error("Audio upload failed.")

        elif tab == "Record Voice":
            st.subheader("Record Your Voice")
            if "recording" not in st.session_state:
                st.session_state.recording = False
            if st.button("Start Recording"):
                st.session_state.recording = True
                st.info("Recording... Click 'Stop Recording' to finish.")
                fs = 44100
                seconds = 5
                st.session_state.recording_audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
                sd.wait()
                st.session_state.recording = False
                st.success("Recording finished.")
            if st.button("Upload Recording"):
                if "recording_audio" in st.session_state:
                    wav_bytes = BytesIO()
                    sf.write(wav_bytes, st.session_state.recording_audio, samplerate=44100, format='WAV')
                    wav_bytes.seek(0)
                    file_payload = {
                        "audio_file": ("recorded.wav", wav_bytes.read(), "audio/wav")
                    }
                    data_payload = {"user_id": user["id"], "voice_name": "Recorded Voice"}
                    res = requests.post(f"{API_URL}/upload_audio", files=file_payload, data=data_payload)
                    if res.status_code == 200:
                        st.success("Recording uploaded successfully!")
                    else:
                        st.error("Recording upload failed.")

        elif tab == "Generate AI Voice":
            st.subheader("Generate AI Voice")
            text = st.text_area("Enter text to synthesize")
            voice_id = st.number_input("Voice ID (e.g., 1)", value=1, step=1)
            if st.button("Generate Voice"):
                payload = {"voice_id": voice_id, "text": text}
                res = requests.post(f"{API_URL}/generate_audio", json=payload)
                if res.status_code == 200:
                    audio_bytes = res.content
                    st.audio(audio_bytes, format="audio/wav")
                    st.success("Audio generated successfully!")
                else:
                    st.error("Voice generation failed.")