import streamlit as st
import requests
import streamlit.components.v1 as components

API_URL = "http://localhost:8000"

st.set_page_config(page_title="EchoMe", page_icon="🎤", layout="centered")

if "user" not in st.session_state:
    st.session_state["user"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "Home"

if st.session_state["page"] == "Home":
    st.title("EchoMe")
    st.write("Welcome to EchoMe! Please select an option below:")
    if st.button("Sign Up"):
        st.session_state["page"] = "Sign Up"
        st.rerun()
    if st.button("Log In"):
        st.session_state["page"] = "Log In"
        st.rerun()

elif st.session_state["page"] == "Sign Up":
    st.title("Sign Up")
    username = st.text_input("Choose a Username")
    password = st.text_input("Choose a Password", type="password")
    if st.button("Create Account"):
        if username and password:
            res = requests.post(f"{API_URL}/signup", json={"username": username, "password": password})
            if res.status_code == 200:
                st.success("Signup successful! Redirecting to Log In...")
                st.session_state["page"] = "Log In"
                st.rerun()
            else:
                st.error(res.json().get("detail", "Signup failed."))
        else:
            st.error("Please provide a username and password.")

elif st.session_state["page"] == "Log In":
    st.title("Log In")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Log In"):
        if username and password:
            res = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
            if res.status_code == 200:
                st.session_state["user"] = res.json()
                st.success("Logged in! Redirecting to Dashboard...")
                st.session_state["page"] = "Dashboard"
                st.rerun()
            else:
                st.error(res.json().get("detail", "Login failed."))
        else:
            st.error("Please enter your username and password.")

elif st.session_state["page"] == "Dashboard":
    user = st.session_state["user"]
    if not user:
        st.error("You need to log in first.")
        if st.button("Go to Log In"):
            st.session_state["page"] = "Log In"
            st.rerun()
    else:
        st.title("Dashboard")
        st.write(f"Welcome, {user['username']}!")
        func = st.selectbox("Select Function", ["Upload Audio", "Record Voice", "Generate AI Voice"])

        if func == "Upload Audio":
            voice_name = st.text_input("Voice Name", value="Uploaded Voice")
            file = st.file_uploader("Choose WAV file", type=["wav"])
            if st.button("Upload Audio") and file:
                form = {"user_id": user["id"], "voice_name": voice_name}
                files = {"audio_file": (file.name, file.read(), "audio/wav")}
                res = requests.post(f"{API_URL}/upload_audio", data=form, files=files)
                if res.status_code == 200:
                    st.success("Uploaded successfully.")
                else:
                    st.error("Upload failed.")

        elif func == "Record Voice":
            st.subheader("🎙️ Record Your Voice")
            st.info("Please ensure you're in a quiet environment and speak clearly. EchoMe will use this audio to build a voice clone.")
            st.markdown("**Please read this aloud while recording:**")
            st.write("> “This is my voice for EchoMe. I am speaking clearly and naturally so the app can learn how I sound.”")
            voice_name = st.text_input("Voice Name", value="Recorded Voice")

            if voice_name.strip():
                components.html(f"""
                    <div style="text-align:center; font-family: Arial;">
                        <div id="rec_status" style="color:red; font-weight:bold; margin-bottom:10px;"></div>
                        <audio id="player" controls style="width:80%; margin-bottom:10px;"></audio><br>
                        <button onclick="startRecording()" style="padding:10px 20px; margin-right:10px; border:none; background:#0073e6; color:white; border-radius:5px;">Start Recording</button>
                        <button onclick="stopRecording()" style="padding:10px 20px; border:none; background:#e60000; color:white; border-radius:5px;">Stop & Upload</button>
                        <p id="ios_warning_text" style="color:orange; font-weight:bold; margin-top:10px; display:none;"></p>
                    </div>
                    <script>
                        let mediaRecorder;
                        let audioChunks = [];
                        const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);

                        async function startRecording() {{
                            try {{
                                const stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                                document.getElementById("rec_status").innerText = "🔴 Recording...";
                                mediaRecorder = new MediaRecorder(stream);
                                mediaRecorder.start();
                                audioChunks = [];

                                mediaRecorder.ondataavailable = e => {{
                                    audioChunks.push(e.data);
                                }};

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
                                    }}).then(response => {{
                                        if (response.ok) {{
                                            alert("✅ Recording uploaded successfully!");
                                            if (isIOS) {{
                                                document.getElementById("ios_warning_text").style.display = "block";
                                                document.getElementById("ios_warning_text").innerText = "⚠️ You won't be able to hear your recording on iOS due to Safari limitations.";
                                            }}
                                        }} else {{
                                            alert("❌ Upload failed.");
                                        }}
                                    }});
                                }};
                            }} catch (err) {{
                                alert("🎙️ Microphone access denied or not available.");
                            }}
                        }}

                        function stopRecording() {{
                            if (mediaRecorder && mediaRecorder.state === "recording") {{
                                mediaRecorder.stop();
                            }}
                        }}
                    </script>
                """, height=410)
            else:
                st.warning("Please enter a voice name before recording.")

        elif func == "Generate AI Voice":
            st.subheader("Generate AI Voice")
            voices_res = requests.get(f"{API_URL}/voices", params={"user_id": user["id"]})
            if voices_res.status_code == 200:
                voices = voices_res.json()
                if voices:
                    options = {v["voice_name"]: v["id"] for v in voices}
                    selected = st.selectbox("Select Voice", options.keys())
                    text = st.text_area("Text to synthesize")
                    if st.button("Generate Voice") and text:
                        payload = {"voice_id": options[selected], "text": text}
                        res = requests.post(f"{API_URL}/generate_audio", json=payload)
                        if res.status_code == 200:
                            st.audio(res.content, format="audio/wav")
                            st.success("Audio generated successfully.")
                        else:
                            st.error("Generation failed.")
                else:
                    st.warning("No voices found.")
            else:
                st.error("Failed to load voices.")
