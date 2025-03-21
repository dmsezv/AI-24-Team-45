import io
from typing import Annotated, List
import cv2
from loguru import logger
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import StreamingResponse
from app_utils.image_processing import read_image
from app_utils.model_manager import ModelManager
from app_models.detection_result import DetectionResult

router = APIRouter(tags=["detection"], prefix="/detect")


@router.post("/coordinates", response_model=List[DetectionResult])
async def detect_transport_coordinates(
    file: Annotated[UploadFile, File(...)],
    model_manager: ModelManager = Depends()
) -> List[DetectionResult]:
    """Detect transport coordinates in the uploaded image."""
    logger.info("Received request for /detect/")
    try:
        image = read_image(await file.read())
        results = model_manager.detect(image)
        detections = results.pandas().xyxy[0].to_dict(orient="records")
        return [DetectionResult(**detection) for detection in detections]
    except Exception as e:
        logger.error(f"Error in detect_transport_coordinates: {e}")
        raise HTTPException(status_code=500, detail="Detection failed") from e


@router.post("/image")
async def detect_transport_image(
    file: Annotated[UploadFile, File(...)],
    model_manager: ModelManager = Depends()
) -> StreamingResponse:
    """Detect transport in the uploaded image and return the image with bounding boxes."""
    logger.info("Received request for /detect/image/")
    try:
        image = read_image(await file.read())
        results = model_manager.detect(image)
        detections = results.pandas().xyxy[0].to_dict(orient="records")

        for detection in detections:
            x1, y1, x2, y2 = (
                int(detection['xmin']), int(detection['ymin']),
                int(detection['xmax']), int(detection['ymax'])
            )
            label = detection['name']
            confidence = detection['confidence']
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                image, f"{label} {confidence:.2f}", (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2
            )

        _, img_encoded = cv2.imencode('.jpg', image)
        return StreamingResponse(io.BytesIO(img_encoded.tobytes()), media_type="image/jpeg")
    except Exception as e:
        logger.error(f"Error in detect_transport_image: {e}")
        raise HTTPException(status_code=500, detail="Image processing failed") from e
