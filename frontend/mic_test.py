import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode

st.title("Mic Test")

webrtc_streamer(
    key="mic-test",
    mode=WebRtcMode.SENDRECV,
    media_stream_constraints={"audio": True, "video": False},
)