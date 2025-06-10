import streamlit as st
import requests, io, base64
import streamlit.components.v1 as components

API_URL = "http://localhost:8000"

st.set_page_config(page_title="EchoMe", page_icon="🎤", layout="centered")

st.markdown(
    """
    <style>
        .echo-btn {
            background-color:#0066cc;color:white;border:none;
            padding:0.6rem 1.2rem;margin:0.25rem;border-radius:5px;
            font-weight:600;cursor:pointer;
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

col1, col2, col3 = st.columns([1, 1, 6])
with col3:
    if state.get("user"):
        st.markdown(f"Logged in as **{state['user']['username']}**", unsafe_allow_html=True)
    else:
        st.markdown("&nbsp;", unsafe_allow_html=True)

if state["page"] == "Home":
    st.markdown("<div class='echo-banner'>🏠 EchoMe Home</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="large")
    if c1.button("🔐 Log In"):
        state["page"] = "Log In"; st.rerun()
    if c2.button("📝 Sign Up"):
        state["page"] = "Sign Up"; st.rerun()

elif state["page"] == "Sign Up":
    st.markdown("<div class='echo-banner'>📝 Sign Up</div>", unsafe_allow_html=True)
    u, p = st.text_input("Username"), st.text_input("Password", type="password")
    if st.button("Create Account"):
        if u and p:
            r = requests.post(f"{API_URL}/signup", json={"username": u, "password": p})
            if r.status_code == 200:
                st.success("Account created! You can log in now.")
                state["page"] = "Log In"; st.rerun()
            else:
                st.error(r.json().get("detail", "Signup failed."))
    st.button("⬅ Back to Home", on_click=lambda: state.update(page="Home"))

elif state["page"] == "Log In":
    st.markdown("<div class='echo-banner'>🔐 Log In</div>", unsafe_allow_html=True)
    u, p = st.text_input("Username"), st.text_input("Password", type="password")
    if st.button("Log In"):
        if u and p:
            r = requests.post(f"{API_URL}/login", json={"username": u, "password": p})
            if r.status_code == 200:
                state["user"] = r.json(); state["page"] = "Dashboard"; st.rerun()
            else:
                st.error(r.json().get("detail", "Login failed."))
    st.button("⬅ Back to Home", on_click=lambda: state.update(page="Home"))

elif state["page"] == "Dashboard":
    user = state.get("user")
    if not user: state["page"] = "Home"; st.rerun()

    st.markdown("<div class='echo-banner'>📂 Dashboard</div>", unsafe_allow_html=True)
    task = st.selectbox("", ["Upload Voice", "Record Voice", "Generate AI Voice"], label_visibility="collapsed")
    st.divider()

    if task == "Upload Voice":
        vname = st.text_input("Voice name", value="My Voice")
        file = st.file_uploader("Upload a WAV file", type=["wav"])
        if st.button("Upload") and file:
            form = {"user_id": user["id"], "voice_name": vname}
            files = {"audio_file": (file.name, file.read(), "audio/wav")}
            if requests.post(f"{API_URL}/upload_audio", data=form, files=files).status_code == 200:
                st.success("Voice uploaded!")

    elif task == "Record Voice":
        vname = st.text_input("Voice name", value="Recorded")
        st.markdown("#### 🎙️ Recording instructions")
        st.info(
            "Record in a quiet place and read:\n\n"
            "> *“Hi, I’m testing my voice. This is a short sentence for calibration.”*"
        )
        components.html(
            f"""
            <div style="text-align:center;padding-top:1rem">
                <div id="rec_status" style="font-weight:bold;color:#d00000"></div>
                <audio id="player" controls style="width:80%;margin-top:10px"></audio><br>
                <button class="echo-btn" onclick="start()">Start Recording</button>
                <button class="echo-btn" onclick="stop()">Stop & Upload</button>
            </div>
            <script>
                let mr, chunks=[];
                async function start(){{
                    const s=await navigator.mediaDevices.getUserMedia({{audio:true}});
                    document.getElementById('rec_status').innerText='🔴 Recording...';
                    mr=new MediaRecorder(s);chunks=[];
                    mr.ondataavailable=e=>chunks.push(e.data);
                    mr.onstop=upload;mr.start();
                }}
                function stop(){{ mr?.state==='recording'&&mr.stop(); }}
                function upload(){{
                    document.getElementById('rec_status').innerText='';
                    const blob=new Blob(chunks,{{type:'audio/wav'}});
                    document.getElementById('player').src=URL.createObjectURL(blob);
                    const fd=new FormData();
                    fd.append('user_id','{user["id"]}');
                    fd.append('voice_name','{vname}');
                    fd.append('audio_file',blob,'rec.wav');
                    fetch('{API_URL}/upload_audio',{{method:'POST',body:fd}});
                }}
            </script>
            """,
            height=350,
        )

    else:
        r = requests.get(f"{API_URL}/voices", params={"user_id": user["id"]})
        if r.status_code != 200:
            st.error("Failed to fetch voices.")
        else:
            voices = r.json()
            if not voices:
                st.warning("No voices found.")
            else:
                mapping = {v["voice_name"]: v["id"] for v in voices}
                vid = mapping[st.selectbox("Select a voice", mapping.keys())]
                text = st.text_area("Text to synthesize", height=150)
                if st.button("Generate") and text:
                    res = requests.post(f"{API_URL}/generate_audio", json={"voice_id": vid, "text": text})
                    if res.status_code == 200:
                        uri = res.json().get("audio", "")
                        if uri.startswith("data:audio/wav;base64,"):
                            b64 = uri.split(",", 1)[1]
                            data = io.BytesIO(base64.b64decode(b64)); data.name = "generated.wav"
                            st.audio(data, format="audio/wav")
                        else:
                            st.error("Invalid audio received.")
                    else:
                        st.error("Generation failed.")

    st.divider()
    st.button("⬅ Log Out & Return Home", on_click=lambda: state.update(page="Home", user=None))
