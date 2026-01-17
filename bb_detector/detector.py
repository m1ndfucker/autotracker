# bb_detector/detector.py
"""
OCR-based death detection with streak confirmation.

Inspired by:
- https://github.com/monkey-tang/Automatic-Multi-Game-Death-Counter (streak-based, fuzzy matching)
- https://github.com/Jan-9C/deathcounter_ocr (OCR approach)

Config structure (games_config style):
- settings.consecutive_hits: int (default 2)
- settings.fuzzy_ocr_matching: bool (default True)
- games.{current_game}.keywords: List[str]
- games.{current_game}.tesseract_config: str
- current_game: str (e.g. "Bloodborne", "Dark Souls 3")
"""
import cv2
import numpy as np
from typing import Tuple, Optional, List

from .config import Config


class DeathDetector:
    """
    OCR-based death detector with streak confirmation.

    Config structure (games_config style):
    - settings.consecutive_hits: int
    - settings.fuzzy_ocr_matching: bool
    - games.{current_game}.keywords: List[str]
    - games.{current_game}.tesseract_config: str
    - current_game: str
    """

    # Default keywords (fallback if not in config)
    DEFAULT_KEYWORDS: List[str] = [
        "YOUDIED", "YOU DIED", "Y0UDIED", "YOUD1ED", "Y0UD1ED",
        "ТЫМЕРТВ", "ТЫ МЕРТВ", "ТЫМЁРТВ",
        "YOUDLED", "YOUOIED", "Y0UD13D",
    ]

    def __init__(self, config: Config):
        self.config = config

        # Load settings from config (games_config style)
        self._load_settings()

        # OCR availability flag
        self._ocr_available = self._check_ocr()

        # Last detection method (for debugging)
        self.last_method: Optional[str] = None
        self.last_confidence: float = 0.0

    def _load_settings(self):
        """Load settings from config (games_config style)."""
        # Streak-based confirmation
        self.consecutive_hits = 0
        self.required_streak = self.config.get('settings.consecutive_hits', 2)

        # Fuzzy OCR matching (O→0, I→1, etc.)
        self.fuzzy_matching = self.config.get('settings.fuzzy_ocr_matching', True)

        # Get current game settings
        current_game = self.config.get('current_game', 'Bloodborne')
        game_config = self.config.get(f'games.{current_game}', {})

        # Keywords from current game (or defaults)
        self.keywords = game_config.get('keywords', self.DEFAULT_KEYWORDS)

        # Tesseract config from current game
        self.tesseract_config = game_config.get(
            'tesseract_config',
            '--oem 3 --psm 6'
        )

    def _check_ocr(self) -> bool:
        """Check if pytesseract is available."""
        try:
            import pytesseract
            # Try to get version to verify tesseract is installed
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def reload(self, config: Config):
        """Reload configuration."""
        self.config = config
        self._load_settings()
        self.consecutive_hits = 0

    def check_death(self, frame: np.ndarray) -> Tuple[bool, float]:
        """
        Check for death using OCR detection with streak confirmation.

        Args:
            frame: BGR/RGB image frame to analyze

        Returns:
            Tuple of (is_death_confirmed, confidence)
            is_death_confirmed is True only after required_streak consecutive detections
        """
        if frame is None:
            return False, 0.0

        # OCR detection only
        if self._ocr_available:
            ocr_detected, ocr_text = self._ocr_detect(frame)
            if ocr_detected:
                return self._confirm_detection(True, 1.0, f"ocr:{ocr_text}")

        # No detection - reset streak
        return self._confirm_detection(False, 0.0, None)

    def _confirm_detection(
        self,
        detected: bool,
        confidence: float,
        method: Optional[str]
    ) -> Tuple[bool, float]:
        """
        Apply streak-based confirmation to reduce false positives.

        Requires `required_streak` consecutive detections before confirming.
        """
        if detected:
            self.consecutive_hits += 1
            self.last_method = method
            self.last_confidence = confidence
        else:
            self.consecutive_hits = 0
            self.last_method = None
            self.last_confidence = confidence

        # Check if we have enough consecutive hits
        confirmed = self.consecutive_hits >= self.required_streak

        if confirmed:
            # Reset after confirmation (to avoid repeated triggers)
            self.consecutive_hits = 0

        return confirmed, confidence

    def _ocr_detect(self, frame: np.ndarray) -> Tuple[bool, str]:
        """
        Perform OCR detection on the frame.

        Uses tesseract_config from current game settings.

        Returns:
            Tuple of (detected, recognized_text)
        """
        try:
            import pytesseract
            from PIL import Image

            # Preprocess for better OCR
            if len(frame.shape) == 3:
                gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            else:
                gray = frame

            # Apply threshold to get high-contrast text
            _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

            # Also try inverted (white text on dark background)
            _, thresh_inv = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)

            # Use tesseract config from current game
            ocr_config = self.tesseract_config

            all_text = []

            # Try both thresholded images
            for img in [thresh, thresh_inv]:
                pil_img = Image.fromarray(img)
                text = pytesseract.image_to_string(pil_img, config=ocr_config)
                all_text.append(text.strip())

                if self._contains_keyword(text):
                    return True, text.strip()[:50]  # Return first 50 chars

            # Return combined text for debugging even if no match
            return False, ' | '.join(filter(None, all_text))[:50]

        except Exception as e:
            return False, f"error:{str(e)[:30]}"

    def _contains_keyword(self, text: str) -> bool:
        """
        Check if text contains any death keyword from current game config.

        If fuzzy_ocr_matching is enabled (default), applies common OCR error corrections:
        0 -> O, 1 -> I, 3 -> E, 5 -> S, 7 -> T

        Uses keywords from games.{current_game}.keywords
        """
        # Normalize: uppercase, remove spaces and non-alphanumeric
        normalized = ''.join(c for c in text.upper() if c.isalnum())

        # Apply fuzzy OCR correction if enabled
        if self.fuzzy_matching:
            # Common OCR error corrections (as per FUZZY_MATCHING_GUIDE.md)
            corrected = (
                normalized
                .replace('0', 'O')
                .replace('1', 'I')
                .replace('3', 'E')
                .replace('5', 'S')
                .replace('7', 'T')
            )
        else:
            corrected = normalized

        # Use keywords from current game config
        for keyword in self.keywords:
            kw_normalized = keyword.replace(' ', '').upper()

            # Check both original and corrected text
            if kw_normalized in normalized or kw_normalized in corrected:
                return True

        return False

    def check_death_region(
        self,
        frame: np.ndarray,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> Tuple[bool, float]:
        """
        Check for death in a specific region of the frame.

        Args:
            frame: Full frame image
            region: Optional tuple of (x, y, width, height) to crop

        Returns:
            Tuple of (is_death_confirmed, confidence)
        """
        if region:
            x, y, w, h = region
            frame = frame[y:y+h, x:x+w]

        return self.check_death(frame)

    def test_detection(self, frame: np.ndarray) -> dict:
        """
        Test detection on a frame without streak confirmation.

        Useful for calibration UI to show immediate results.

        Returns:
            Dict with 'ocr_match', 'ocr_text', 'keywords_found', 'fuzzy_enabled'
        """
        result = {
            'ocr_match': False,
            'ocr_text': '',
            'keywords_found': [],
            'fuzzy_enabled': self.fuzzy_matching
        }

        if frame is None:
            return result

        # OCR (if available)
        if self._ocr_available:
            try:
                import pytesseract
                from PIL import Image

                if len(frame.shape) == 3:
                    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
                else:
                    gray = frame

                _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
                pil_img = Image.fromarray(thresh)
                text = pytesseract.image_to_string(pil_img, config=self.tesseract_config)

                result['ocr_text'] = text.strip()
                result['ocr_match'] = self._contains_keyword(text)

                # Find which keywords matched
                normalized = ''.join(c for c in text.upper() if c.isalnum())
                for kw in self.keywords:
                    if kw.replace(' ', '') in normalized:
                        result['keywords_found'].append(kw)

            except Exception:
                pass

        return result
