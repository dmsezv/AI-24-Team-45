import streamlit as st

st.title("Tracking Object on Live Camera in Belgrade")

video_url = "https://streamer.devnet.rs/hls/slavija.m3u8"

st.markdown("""
### Camera on Slavia Square
""")

st.video(video_url)


with st.expander("Settings"):
    detect_classes = st.multiselect(
        "Tracked classes",
        ["Bus", "Car", "Train", "Motorcycle", "Bicycle"],
        default=["Bus", "Train"]
    )

start_detection = st.button("Start Tracking", key="start_tracking")

if start_detection:
    st.info("Функция детекции объектов будет реализована в следующей части.")

    with st.spinner("Подключение к API..."):
        try:
            pass
        except Exception as e:
            st.error(f"Ошибка при подключении к API: {e}")
