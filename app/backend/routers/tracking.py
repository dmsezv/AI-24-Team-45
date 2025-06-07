import cv2
import asyncio
import time
import threading
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from app_utils.model_manager import ModelManager
from app_utils.image_processing import draw
from app_utils.ffmpeg_service import FFmpegReader

router = APIRouter(prefix="/stream", tags=["streaming"])

current, lock = None, threading.Lock()


@router.get("/video-feed")
async def video_feed(
    url: str,
    width: int = 640,
    height: int = 480,
    fps: int = 7,
    # confidence: float = 0.5,
    classes: Optional[str] = None,
    model: ModelManager = Depends()
):
    stop_stream()
    allowed = [c.strip() for c in classes.split(",")] if classes else None
    reader = FFmpegReader(url, width, height, fps)

    if not reader.start():
        raise RuntimeError("FFmpeg start failed")

    global current
    with lock:
        current = reader
    period = 1 / fps

    async def stream():
        try:
            while reader.running:
                t0 = time.perf_counter()
                frame = reader.get()

                if frame is None:
                    await asyncio.sleep(0.005)
                    continue

                det = await asyncio.to_thread(model.track, frame)
                draw(frame, det, allowed)
                _, enc = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + enc.tobytes() + b"\r\n"

                dt = time.perf_counter() - t0
                if dt < period:
                    await asyncio.sleep(period - dt)
        finally:
            stop_stream()

    return StreamingResponse(stream(), media_type="multipart/x-mixed-replace; boundary=frame")


def stop_stream():
    global current
    with lock:
        if current:
            current.stop()
            current = None
            return True
    return False


@router.get("/stop")
async def stop():
    return JSONResponse({"stopped": stop_stream()})


@router.get("/status")
async def status():
    with lock:
        running = current is not None and current.running
    return {"running": running}


@router.get("/cameras")
async def cams() -> Dict[str, Any]:
    return {"cameras": [{"id": "0", "name": "Веб-камера"}]}