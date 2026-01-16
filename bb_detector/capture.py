# bb_detector/capture.py
import numpy as np
from .platform_utils import get_platform

class ScreenCapture:
    def __init__(self, monitor: int = 0, fps: int = 10):
        self.monitor = monitor
        self.fps = fps
        self._platform = get_platform()
        self._backend = None
        self._camera = None
        self._sct = None
        self._monitor_info = None
        self._resolution = None

        self._init_backend()

    def _init_backend(self):
        # Try bettercam on Windows
        if self._platform == 'windows':
            try:
                import bettercam
                self._backend = 'bettercam'
                self._camera = bettercam.create(output_idx=self.monitor)
                return
            except (ImportError, Exception):
                pass

        # Fallback: mss (cross-platform)
        import mss
        self._backend = 'mss'
        self._sct = mss.mss()
        # mss monitors: 0 = all, 1+ = individual
        monitor_idx = min(self.monitor + 1, len(self._sct.monitors) - 1)
        self._monitor_info = self._sct.monitors[monitor_idx]
        self._resolution = (self._monitor_info['width'], self._monitor_info['height'])

    def start(self):
        if self._backend == 'bettercam' and self._camera:
            self._camera.start(target_fps=self.fps)

    def stop(self):
        if self._backend == 'bettercam' and self._camera:
            self._camera.stop()

    def grab(self) -> np.ndarray | None:
        if self._backend == 'bettercam':
            frame = self._camera.get_latest_frame()
            if frame is not None:
                self._resolution = (frame.shape[1], frame.shape[0])
            return frame

        elif self._backend == 'mss':
            screenshot = self._sct.grab(self._monitor_info)
            frame = np.array(screenshot)
            # Remove alpha channel and convert BGRA -> RGB
            frame = frame[:, :, :3]
            frame = frame[:, :, ::-1].copy()
            return frame

        return None

    def grab_region(self, x: int, y: int, w: int, h: int) -> np.ndarray | None:
        if self._backend == 'bettercam':
            frame = self.grab()
            if frame is not None:
                return frame[y:y+h, x:x+w]
            return None

        elif self._backend == 'mss':
            region = {
                'left': self._monitor_info['left'] + x,
                'top': self._monitor_info['top'] + y,
                'width': w,
                'height': h
            }
            screenshot = self._sct.grab(region)
            frame = np.array(screenshot)[:, :, :3][:, :, ::-1].copy()
            return frame

        return None

    @property
    def resolution(self) -> tuple[int, int]:
        if self._resolution:
            return self._resolution
        return (1920, 1080)

    @property
    def backend(self) -> str:
        return self._backend
