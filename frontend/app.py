import streamlit as st
import requests
import numpy as np
from io import BytesIO
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import soundfile as sf

API_URL = "http://localhost:8000"

if "user" not in st.session_state:
    st.session_state["user"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "Home"

nav_choice = st.sidebar.selectbox("Navigation", ["Home", "Sign Up", "Log In", "Dashboard"], key="nav_menu")
st.session_state["page"] = nav_choice

if st.session_state["page"] == "Home":
    st.title("EchoMe")
    st.write("Welcome to EchoMe. Please sign up or log in to continue.")

elif st.session_state["page"] == "Sign Up":
    st.title("Sign Up")
    username = st.text_input("Username", key="signup_username")
    password = st.text_input("Password", type="password", key="signup_password")
    if st.button("Sign Up", key="signup_btn"):
        res = requests.post(f"{API_URL}/signup", json={"username": username, "password": password})
        if res.status_code == 200:
            st.success("Signup successful. Please log in.")
            st.session_state["page"] = "Log In"
        else:
            st.error(res.json().get("detail", "Signup failed."))

elif st.session_state["page"] == "Log In":
    st.title("Log In")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Log In", key="login_btn"):
        res = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
        if res.status_code == 200:
            st.session_state["user"] = res.json()
            st.success("Login successful.")
            st.session_state["page"] = "Dashboard"
        else:
            st.error(res.json().get("detail", "Login failed."))

elif st.session_state["page"] == "Dashboard":
    if st.session_state["user"] is None:
        st.error("Please log in first.")
    else:
        user = st.session_state["user"]
        st.title("Dashboard")
        st.write(f"Welcome, {user['username']}")
        func = st.selectbox("Select Function", ["Upload Audio", "Record Voice", "Generate AI Voice"], key="dashboard_func")
        
        if func == "Upload Audio":
            st.subheader("Upload an Audio File")
            uploaded_file = st.file_uploader("Choose a WAV file", type=["wav"], key="upload_file")
            if st.button("Upload Audio", key="upload_audio_btn") and uploaded_file is not None:
                form = {"user_id": user["id"], "voice_name": "Uploaded Voice"}
                files = {"audio_file": (uploaded_file.name, uploaded_file.getvalue(), "audio/wav")}
                res = requests.post(f"{API_URL}/upload_audio", data=form, files=files)
                if res.status_code == 200:
                    st.success("Audio uploaded successfully.")
                else:
                    st.error("Upload failed.")
        
        elif func == "Record Voice":
            st.subheader("Record Your Voice")
            rec_ctx = webrtc_streamer(key="recorder", mode=WebRtcMode.SENDONLY, audio_receiver_size=256)
            if rec_ctx.audio_receiver and st.button("Stop and Upload Recording", key="upload_record_btn"):
                frames = rec_ctx.audio_receiver.get_frames(timeout=1)
                if frames:
                    audio = np.concatenate([f.to_ndarray() for f in frames])
                    wav_io = BytesIO()
                    sf.write(wav_io, audio, samplerate=44100, format="WAV")
                    wav_io.seek(0)
                    files = {"audio_file": ("recorded.wav", wav_io.read(), "audio/wav")}
                    form = {"user_id": user["id"], "voice_name": "Recorded Voice"}
                    res = requests.post(f"{API_URL}/upload_audio", data=form, files=files)
                    if res.status_code == 200:
                        st.success("Recording uploaded successfully.")
                    else:
                        st.error("Recording upload failed.")
        
        elif func == "Generate AI Voice":
            st.subheader("Generate AI Voice")
            voices_res = requests.get(f"{API_URL}/voices", params={"user_id": user["id"]})
            if voices_res.status_code == 200:
                voices = voices_res.json()
                if voices:
                    options = {v["voice_name"]: v["id"] for v in voices}
                    selected_voice = st.selectbox("Select Voice", list(options.keys()), key="voice_dropdown")
                    voice_id = options[selected_voice]
                    text = st.text_area("Enter text to synthesize", key="synth_text")
                    if st.button("Generate Voice", key="generate_btn") and text:
                        payload = {"voice_id": voice_id, "text": text}
                        res = requests.post(f"{API_URL}/generate_audio", json=payload)
                        if res.status_code == 200:
                            st.audio(res.content, format="audio/wav")
                            st.success("Audio generated successfully.")
                        else:
                            st.error("Voice generation failed.")
                else:
                    st.error("No voices found. Please upload or record a voice first.")
            else:
                st.error("Failed to retrieve voices.")
