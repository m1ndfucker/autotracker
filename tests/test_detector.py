# tests/test_detector.py
import pytest
import numpy as np
import cv2
from pathlib import Path

def test_detector_init():
    """Detector initializes with config"""
    from bb_detector.detector import DeathDetector
    from bb_detector.config import Config

    config = Config()
    detector = DeathDetector(config)

    assert detector.threshold == 0.75

def test_detector_check_death_no_match():
    """check_death returns False for blank frame"""
    from bb_detector.detector import DeathDetector
    from bb_detector.config import Config

    config = Config()
    detector = DeathDetector(config)

    # Create blank frame
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)

    is_dead, confidence = detector.check_death(frame)

    assert is_dead == False
    assert confidence < 0.5
