import time
import requests
import streamlit as st
from urllib.parse import quote
from settings.config import API_BASE_URL


CAM_URL = "https://streamer.devnet.rs/hls/slavija.m3u8"


st.title("Tracking Object on Live Camera in Belgrade")

if "running" not in st.session_state:
    st.session_state.running = False

class_list = [
    "car",
    "bus",
    "truck",
    "motorcycle",
    "bicycle"
]


if not st.session_state.running:
    with st.expander("⚙ Settings", expanded=True):
        sel = st.multiselect("Classes to track", class_list, ["car", "bus"])
        fps = st.slider("FPS", 5, 30, 10)
        conf = st.slider("Confidence", 0.1, 1.0, 0.15)
        # st.select_slider("Ширина",  [320, 480, 640, 800, 1024], 640)
        # st.select_slider("Высота",   [240, 360, 480, 600, 720],  480)

    if st.button("🔍 Start tracking"):
        st.session_state.running = True
        st.session_state.ts = int(time.time())
        st.rerun()
else:
    if st.button("⏹ Stop tracking"):
        try:
            requests.get(f"{API_BASE_URL}/stream/stop", timeout=1)
        finally:
            st.session_state.running = False
            st.rerun()

    st.markdown("""
    <div style="background-color: rgb(38, 39, 48); padding: 10px; border-radius: 5px;">
        <b>Current parameters:</b><br/>
        FPS: {}<br/>
        Confidence: {}<br/>
        Classes tracking: {}
    </div>
    """.format(
        st.session_state.get('fps', 10),
        st.session_state.get('conf', 0.15),
        ', '.join(st.session_state.get('sel', ['car', 'bus']))
    ), unsafe_allow_html=True)

if not st.session_state.running:
    st.session_state.sel = sel
    st.session_state.fps = fps
    st.session_state.conf = conf

if st.session_state.running:
    width = 640
    height = 480

    classes = ",".join(c for c in st.session_state.sel)

    stream_url = (
        f"{API_BASE_URL}/stream/video-feed"
        f"?url={quote(CAM_URL)}"
        f"&width={width}&height={height}&fps={st.session_state.fps}"
        f"&confidence={st.session_state.conf}&classes={classes}&_t={st.session_state.ts}"
    )
    st.markdown("### 🎬 Video on live camera Slavija")
    st.markdown(
        f"""
        <center>
            <img src="{stream_url}" width="{width}" height="{height}">
        </center>
        """,
        unsafe_allow_html=True
    )
