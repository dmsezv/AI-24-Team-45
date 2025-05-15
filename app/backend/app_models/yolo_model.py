import torch
from loguru import logger
import os
from ultralytics import YOLO


class YOLOModel:
    """A class representing a YOLO model for object detection."""

    def __init__(self, model_name: str, model_path: str):
        """Initialize the YOLO model with the given model path."""
        logger.info(f"Loading YOLO model from {model_path}")
        self.model_name = model_name
        self.model_path = model_path

        base_name = os.path.basename(model_path)

        if base_name.startswith("yolov12"):
            logger.info("Loading YOLOv12 model using ultralytics")
            self.model = YOLO(model_path)
            self.version = "v12"
        else:
            logger.info("Loading YOLOv5 model using torch.hub")
            self.model = torch.hub.load(
                'ultralytics/yolov5',
                'custom',
                path=model_path,
                trust_repo=True,
                force_reload=True
            )
            self.version = "v5"

    def detect(self, image):
        """Run detection on the provided image."""
        logger.info("Running detection on image")
        results = self.model(image)
        return results

    def get_model_info(self):
        """Return information about the model."""
        return {
            "model_name": self.model_name,
            "model_path": self.model_path,
            "version": self.version
        }
