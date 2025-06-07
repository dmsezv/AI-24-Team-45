import cv2
import threading
import subprocess
from loguru import logger
import numpy as np


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