import time
import requests
import streamlit as st
from urllib.parse import quote
from settings.config import API_BASE_URL   # ← ваш .env или config.py

st.title("Tracking Object on Live Camera in Belgrade")

CAM_URL = "https://streamer.devnet.rs/hls/slavija.m3u8"

if "running" not in st.session_state:
    st.session_state.running = False
    st.session_state.ts = None

if st.session_state.running:
    if st.button("⏹ Стоп"):
        try:
            requests.get(f"{API_BASE_URL}/stream/stop", timeout=1)
        finally:
            st.session_state.running = False
            st.session_state.ts = None
            st.rerun()
else:
    if st.button("🔍 Старт детекции"):
        st.session_state.running = True
        st.session_state.ts = int(time.time())
        st.rerun()

class_map = {
    "Автомобиль": "car",
    "Автобус": "bus",
    "Грузовик": "truck",
    "Мотоцикл": "motorcycle",
    "Велосипед": "bicycle"
}

with st.expander("⚙ Параметры"):
    #conf = st.slider("Порог уверенности", 0.1, 1.0, 0.5, 0.05)
    sel = st.multiselect("Классы", list(class_map), ["Автомобиль", "Автобус"])
    #fps = st.slider("FPS", 5, 30, 20)
    #width = st.select_slider("Ширина",  [320, 480, 640, 800, 1024], 640)
    #height = st.select_slider("Высота",   [240, 360, 480, 600, 720],  480)

if st.session_state.running:
    width = 640
    height = 480
    classes = ",".join(class_map[c] for c in sel)
    stream_url = (
        f"{API_BASE_URL}/stream/video-feed"
        f"?url={quote(CAM_URL)}"
        f"&width={width}&height={height}&fps={30}"
        f"&confidence={0.5}&classes={classes}&_t={st.session_state.ts}"
    )
    st.markdown("### 🎬 Видео")
    st.markdown(
        f"""
        <center>
            <img src="{stream_url}" width="{width}" height="{height}">
        </center>
        """,
        unsafe_allow_html=True
    )
