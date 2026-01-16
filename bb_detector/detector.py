# bb_detector/detector.py
import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Optional

from .config import Config


class DeathDetector:
    def __init__(self, config: Config):
        self.config = config
        self.threshold = config.get('detection.death_threshold', 0.75)
        self.template = None
        self.template_gray = None

        self._load_template()

    def _load_template(self):
        # Try custom template first
        custom = self.config.get('templates.death.custom')
        if custom:
            custom_path = Path(custom)
            if custom_path.exists():
                self.template = cv2.imread(str(custom_path))
                if self.template is not None:
                    self.template_gray = cv2.cvtColor(self.template, cv2.COLOR_BGR2GRAY)
                    return

        # Fall back to builtin
        builtin = self.config.get('templates.death.builtin', 'you_died_en.png')

        # Check multiple locations
        possible_paths = [
            Path(__file__).parent.parent / 'assets' / 'templates' / builtin,
            Path.cwd() / 'assets' / 'templates' / builtin,
            Path(__file__).parent / 'assets' / 'templates' / builtin,
        ]

        for template_path in possible_paths:
            if template_path.exists():
                self.template = cv2.imread(str(template_path))
                if self.template is not None:
                    self.template_gray = cv2.cvtColor(self.template, cv2.COLOR_BGR2GRAY)
                    return

        # Create minimal fallback template
        self.template = np.zeros((50, 200, 3), dtype=np.uint8)
        self.template_gray = np.zeros((50, 200), dtype=np.uint8)

    def reload(self, config: Config):
        self.config = config
        self.threshold = config.get('detection.death_threshold', 0.75)
        self._load_template()

    def check_death(self, frame: np.ndarray) -> Tuple[bool, float]:
        if frame is None or self.template_gray is None:
            return False, 0.0

        # Convert to grayscale
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        else:
            gray = frame

        # Resize template if needed (handle different resolutions)
        template = self.template_gray

        # Template matching
        try:
            result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            return max_val >= self.threshold, float(max_val)
        except cv2.error:
            return False, 0.0

    def check_death_region(self, frame: np.ndarray,
                           region: Optional[Tuple[int, int, int, int]] = None) -> Tuple[bool, float]:
        if region:
            x, y, w, h = region
            frame = frame[y:y+h, x:x+w]

        return self.check_death(frame)
