import cv2, asyncio, time, subprocess, threading, numpy as np
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from loguru import logger
from app_utils.model_manager import ModelManager

router = APIRouter(prefix="/stream", tags=["streaming"])

current, lock = None, threading.Lock()


class FFmpegReader:
    def __init__(self, src: str, w: int, h: int, fps: int):
        self.cmd = [
            "ffmpeg",
            "-re",
            "-hwaccel", "videotoolbox",
            "-fflags", "nobuffer",
            "-flags", "low_delay",
            "-i", src,
            "-vf", f"scale={w}:{h},fps={fps}",
            "-f", "mjpeg",
            "-q:v", "1",
            "pipe:1"
        ]

        self.buf, self.proc, self.running = bytearray(), None, False
        self.frm_lock, self.frame = threading.Lock(), None

    def start(self) -> bool:
        if self.running:
            return True
        try:
            self.proc = subprocess.Popen(
                self.cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0
            )
            self.running = True
            threading.Thread(target=self._loop, daemon=True).start()
            logger.info("FFmpeg start OK")

            return True
        except Exception as e:
            logger.error(f"FFmpeg error: {e}")

            return False

    def _loop(self):
        SOI, EOI = b"\xff\xd8", b"\xff\xd9"
        rd = self.proc.stdout.read
        while self.running and self.proc.poll() is None:
            self.buf.extend(rd(8192))
            while True:
                s = self.buf.find(SOI)
                e = self.buf.find(EOI, s + 2)
                if s < 0 or e < 0:
                    break
                jpeg = self.buf[s:e + 2]
                del self.buf[:e + 2]
                img = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
                if img is None:
                    continue
                with self.frm_lock:
                    self.frame = img
        self.running = False

    def get(self):
        with self.frm_lock:
            return self.frame.copy() if self.frame is not None else None

    def stop(self):
        self.running = False
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=2)
            except Exception:
                self.proc.kill()
            self.proc = None
            logger.info("FFmpeg stopped")


def stop_stream():
    global current
    with lock:
        if current:
            current.stop()
            current = None
            return True
    return False


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


def draw(img, res, allowed):
    if hasattr(res, "pandas"):
        for d in res.pandas().xyxy[0].to_dict("records"):
            label = d.get("name", str(d.get("class", "")))
            if allowed and label not in allowed:
                continue
            x1, y1, x2, y2 = map(int, (d["xmin"], d["ymin"], d["xmax"], d["ymax"]))
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img, f"{label} {d['confidence']:.2f}", (x1, y1 - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 2)
    else:
        r = res[0]
        boxes, names = r.boxes, r.names

        track_ids = boxes.id if boxes.id is not None else [None] * len(boxes)

        for xyxy, conf, cls_id, track_id in zip(
                boxes.xyxy, boxes.conf, boxes.cls, track_ids):

            label = names.get(int(cls_id), str(int(cls_id)))
            if allowed and label not in allowed:
                continue

            x1, y1, x2, y2 = map(int, xyxy)
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

            txt = f"{label} {conf:.2f}"
            if track_id is not None:
                txt += f" id:{int(track_id)}"

            cv2.putText(img, txt, (x1, y1-6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 2)


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