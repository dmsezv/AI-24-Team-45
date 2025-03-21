import io
import streamlit as st
import requests
from PIL import Image
from loguru import logger
from settings.config import API_BASE_URL

st.title("Transport Detection on Image")

uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image_container = st.empty()
    image = Image.open(uploaded_file)
    image_container.image(image, caption='Uploaded Image.', use_container_width=True)
    logger.info("Image uploaded")

    if st.button("Detect"):
        logger.info("Detection button clicked")
        try:
            files = {"file": uploaded_file.getvalue()}
            response = requests.post(
                f"{API_BASE_URL}/detect/image/", files=files, timeout=10
            )
            logger.info(f"Request sent to {API_BASE_URL}/detect/image/")

            if response.status_code == 200:
                result_image = Image.open(io.BytesIO(response.content))
                image_container.image(
                    result_image, caption='Detected Image with Bounding Boxes.', use_container_width=True
                )
                logger.info("Detection successful, image displayed")
            else:
                logger.error(f"Detection failed with status code: {response.status_code}")
                st.error("Error in detection process")
        except requests.exceptions.RequestException as e:
            logger.error(f"Exception during detection: {e}")
            st.error("An error occurred during detection")
