import streamlit as st
import requests
import io
import base64
import streamlit.components.v1 as components

API_URL = "http://localhost:8000"

st.set_page_config(page_title="EchoMe", page_icon="🎤", layout="centered")

if "user" not in st.session_state:
    st.session_state["user"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "Home"

if st.session_state["page"] == "Home":
    st.title("EchoMe")
    if st.button("Sign Up"):
        st.session_state["page"] = "Sign Up"
        st.rerun()
    if st.button("Log In"):
        st.session_state["page"] = "Log In"
        st.rerun()

elif st.session_state["page"] == "Sign Up":
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Create Account"):
        if username and password:
            res = requests.post(f"{API_URL}/signup", json={"username": username, "password": password})
            if res.status_code == 200:
                st.session_state["page"] = "Log In"
                st.rerun()
            else:
                st.error(res.json().get("detail", "Signup failed."))

elif st.session_state["page"] == "Log In":
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Log In"):
        if username and password:
            res = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
            if res.status_code == 200:
                st.session_state["user"] = res.json()
                st.session_state["page"] = "Dashboard"
                st.rerun()
            else:
                st.error(res.json().get("detail", "Login failed."))

elif st.session_state["page"] == "Dashboard":
    user = st.session_state["user"]
    func = st.selectbox("Choose", ["Upload Voice", "Record Voice", "Generate AI Voice"])

    if func == "Upload Voice":
        voice_name = st.text_input("Voice Name", value="My Voice")
        file = st.file_uploader("Upload WAV", type=["wav"])
        if st.button("Upload") and file:
            form = {"user_id": user["id"], "voice_name": voice_name}
            files = {"audio_file": (file.name, file.read(), "audio/wav")}
            res = requests.post(f"{API_URL}/upload_audio", data=form, files=files)
            if res.status_code == 200:
                st.success("Uploaded.")

    elif func == "Record Voice":
        voice_name = st.text_input("Voice Name", value="Recorded")

        if voice_name.strip():
            st.markdown("### 🎙️ Voice Recording Instructions")
            st.info(
                "Please record in a **quiet environment**.\n\n"
                "Read the sentence below clearly and naturally:\n\n"
                "> *“Hi, I’m testing my voice. This is a short sentence for calibration. Hope it works well!”*"
            )

            components.html(f"""
                <style>
                    .recorder-wrapper {{
                        text-align: center;
                        padding-top: 1rem;
                    }}
                    .recorder-wrapper button {{
                        background-color: #0066cc;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        font-size: 16px;
                        margin: 10px;
                        border-radius: 5px;
                        cursor: pointer;
                    }}
                    .recorder-wrapper button:hover {{
                        background-color: #0052a3;
                    }}
                    #rec_status {{
                        font-weight: bold;
                        color: #d00000;
                        padding-bottom: 10px;
                    }}
                </style>
                <div class="recorder-wrapper">
                    <div id="rec_status"></div>
                    <audio id="player" controls style="width: 80%; margin-top: 10px;"></audio><br>
                    <button onclick="startRecording()">Start Recording</button>
                    <button onclick="stopRecording()">Stop & Upload</button>
                </div>
                <script>
                    let mediaRecorder;
                    let audioChunks = [];

                    async function startRecording() {{
                        const stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                        document.getElementById("rec_status").innerText = "🔴 Recording...";
                        mediaRecorder = new MediaRecorder(stream);
                        mediaRecorder.start();
                        audioChunks = [];
                        mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
                        mediaRecorder.onstop = () => {{
                            document.getElementById("rec_status").innerText = "";
                            const audioBlob = new Blob(audioChunks, {{ type: 'audio/wav' }});
                            const audioUrl = URL.createObjectURL(audioBlob);
                            document.getElementById("player").src = audioUrl;

                            const formData = new FormData();
                            formData.append("user_id", "{user['id']}");
                            formData.append("voice_name", "{voice_name}");
                            formData.append("audio_file", audioBlob, "recorded.wav");

                            fetch("{API_URL}/upload_audio", {{
                                method: "POST",
                                body: formData
                            }});
                        }};
                    }}

                    function stopRecording() {{
                        if (mediaRecorder && mediaRecorder.state === "recording") {{
                            mediaRecorder.stop();
                        }}
                    }}
                </script>
            """, height=420)

    elif func == "Generate AI Voice":
        res = requests.get(f"{API_URL}/voices", params={"user_id": user["id"]})
        if res.status_code == 200:
            voices = res.json()
            if voices:
                options = {v["voice_name"]: v["id"] for v in voices}
                selected = st.selectbox("Select Voice", options.keys())
                styles = ["default", "whispering", "cheerful", "terrified", "angry", "sad", "friendly"]
                selected_style = st.selectbox("Select Voice Style", styles)
                text = st.text_area("Text")
                if st.button("Generate") and text:
                    payload = {
                        "voice_id": options[selected],
                        "text": text,
                        "style": selected_style
                    }
                    res = requests.post(f"{API_URL}/generate_audio", json=payload)
                    if res.status_code == 200:
                        audio_data_uri = res.json()["audio"]
                        if audio_data_uri.startswith("data:audio"):
                            header, b64data = audio_data_uri.split(",", 1)
                            audio_bytes = io.BytesIO(base64.b64decode(b64data))
                            audio_bytes.name = "generated.wav"
                            st.audio(audio_bytes, format="audio/wav", start_time=0)
                        else:
                            st.error("Invalid audio format.")
                    else:
                        st.error("Generation failed or returned no audio.")
            else:
                st.warning("No voices found.")
        else:
            st.error("Failed to fetch voices.")
