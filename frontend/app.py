import streamlit as st
import requests, io, base64
import streamlit.components.v1 as components

API_URL = "http://localhost:8000"

st.set_page_config(page_title="EchoMe", page_icon="🎤", layout="centered")

st.markdown(
    """
    <style>
        .main { text-align: center; }
        .echo-btn {
            background-color:#0066cc;color:white;border:none;padding:0.6rem 1.2rem;
            margin:0.25rem;border-radius:5px;font-weight:600;cursor:pointer;
        }
        .echo-btn:hover { background:#0052a3; }
        .echo-banner { font-size:2rem;font-weight:700;margin:0.2rem 0 1rem 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

state = st.session_state
state.setdefault("user", None)
state.setdefault("page", "Home")

col_nav1, col_nav2, col_nav3 = st.columns([1, 1, 6])
with col_nav3:
    if state.get("user"):
        st.markdown(
            f"Logged in as **{state['user']['username']}**  |  "
            f"<button class='echo-btn' onclick='window.location.reload()'>Logout</button>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown("&nbsp;", unsafe_allow_html=True)

if state["page"] == "Home":
    st.markdown("<div class='echo-banner'>🏠 EchoMe Home</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")
    with col1:
        if st.button("🔐 Log In", key="home_login", type="primary"):
            state["page"] = "Log In"
            st.rerun()
    with col2:
        if st.button("📝 Sign Up", key="home_signup", type="primary"):
            state["page"] = "Sign Up"
            st.rerun()

elif state["page"] == "Sign Up":
    st.markdown("<div class='echo-banner'>📝 Sign Up</div>", unsafe_allow_html=True)

    username = st.text_input("Choose a username")
    password = st.text_input("Choose a password", type="password")

    col = st.columns([1, 2, 1])[1]
    with col:
        if st.button("Create Account", key="create_account"):
            if username and password:
                r = requests.post(f"{API_URL}/signup", json={"username": username, "password": password})
                if r.status_code == 200:
                    st.success("Account created! You can log in now.")
                    state["page"] = "Log In"
                    st.rerun()
                else:
                    st.error(r.json().get("detail", "Signup failed."))

    st.button("⬅ Back to Home", on_click=lambda: state.update(page="Home"))

elif state["page"] == "Log In":
    st.markdown("<div class='echo-banner'>🔐 Log In</div>", unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    col = st.columns([1, 2, 1])[1]
    with col:
        if st.button("Log In", key="login"):
            if username and password:
                r = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
                if r.status_code == 200:
                    state["user"] = r.json()
                    state["page"] = "Dashboard"
                    st.rerun()
                else:
                    st.error(r.json().get("detail", "Login failed."))

    st.button("⬅ Back to Home", on_click=lambda: state.update(page="Home"))

elif state["page"] == "Dashboard":
    user = state.get("user")
    if not user:
        state["page"] = "Home"
        st.rerun()

    st.markdown("<div class='echo-banner'>📂 Dashboard</div>", unsafe_allow_html=True)

    func = st.selectbox(
        "Choose an action",
        ["Upload Voice", "Record Voice", "Generate AI Voice"],
        index=0,
        label_visibility="collapsed",
    )
    st.divider()

    if func == "Upload Voice":
        voice_name = st.text_input("Voice name", value="My Voice")
        file = st.file_uploader("Upload a WAV file", type=["wav"])
        if st.button("Upload", key="upload_btn") and file:
            form = {"user_id": user["id"], "voice_name": voice_name}
            files = {"audio_file": (file.name, file.read(), "audio/wav")}
            r = requests.post(f"{API_URL}/upload_audio", data=form, files=files)
            if r.status_code == 200:
                st.success("Voice uploaded!")

    elif func == "Record Voice":
        voice_name = st.text_input("Voice name", value="Recorded")
        st.markdown("#### 🎙️ Recording instructions")
        st.info(
            "Record in a **quiet environment** and read the sentence clearly:\n\n"
            "> *“Hi, I’m testing my voice. This is a short sentence for calibration.”*"
        )

        components.html(
            f"""
            <div class="recorder-wrapper" style="text-align:center;padding-top:1rem">
                <div id="rec_status" style="font-weight:bold;color:#d00000"></div>
                <audio id="player" controls style="width:80%;margin-top:10px"></audio><br>
                <button class="echo-btn" onclick="startRecording()">Start Recording</button>
                <button class="echo-btn" onclick="stopRecording()">Stop & Upload</button>
            </div>
            <script>
                let mr, chunks=[];
                async function startRecording(){{
                    const s=await navigator.mediaDevices.getUserMedia({{audio:true}});
                    document.getElementById('rec_status').innerText='🔴 Recording...';
                    mr=new MediaRecorder(s);chunks=[];
                    mr.ondataavailable=e=>chunks.push(e.data);
                    mr.onstop=upload;mr.start();
                }}
                function stopRecording(){{ mr?.state==='recording'&&mr.stop(); }}
                function upload(){{
                    document.getElementById('rec_status').innerText='';
                    const blob=new Blob(chunks,{{type:'audio/wav'}});
                    document.getElementById('player').src=URL.createObjectURL(blob);
                    const fd=new FormData();
                    fd.append('user_id','{user["id"]}');
                    fd.append('voice_name','{voice_name}');
                    fd.append('audio_file',blob,'recorded.wav');
                    fetch('{API_URL}/upload_audio',{{method:'POST',body:fd}});
                }}
            </script>
            """,
            height=350,
        )

    elif func == "Generate AI Voice":
        r = requests.get(f"{API_URL}/voices", params={"user_id": user["id"]})
        if r.status_code != 200:
            st.error("Failed to fetch voices.")
        else:
            voices = r.json()
            if not voices:
                st.warning("No voices found. Upload or record one first.")
            else:
                mapping = {v["voice_name"]: v["id"] for v in voices}
                vid = mapping[st.selectbox("Select a voice", mapping.keys())]
                text = st.text_area("Text to synthesize", height=150)

                if st.button("Generate", key="generate_btn") and text:
                    payload = {"voice_id": vid, "text": text}
                    res = requests.post(f"{API_URL}/generate_audio", json=payload)
                    if res.status_code == 200:
                        uri = res.json().get("audio", "")
                        if uri.startswith("data:audio/wav;base64,"):
                            b64 = uri.split(",", 1)[1]
                            audio_bytes = io.BytesIO(base64.b64decode(b64))
                            audio_bytes.name = "generated.wav"
                            st.audio(audio_bytes, format="audio/wav")
                        else:
                            st.error("Invalid audio received.")
                    else:
                        try:
                            detail = res.json().get("detail", "Generation failed.")
                        except ValueError:
                            detail = f"{res.status_code} {res.reason}"
                        st.error(detail)

    st.divider()
    st.button("⬅ Log Out & Return Home", on_click=lambda: state.update(page="Home", user=None))
