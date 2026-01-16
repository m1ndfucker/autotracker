# tests/test_capture.py
import pytest
import numpy as np

def test_capture_grab_returns_numpy():
    """grab() returns a numpy array"""
    from bb_detector.capture import ScreenCapture

    capture = ScreenCapture(monitor=0)
    frame = capture.grab()

    assert isinstance(frame, np.ndarray)
    assert len(frame.shape) == 3  # Height, Width, Channels
    assert frame.shape[2] == 3    # RGB

def test_capture_resolution():
    """resolution property returns tuple"""
    from bb_detector.capture import ScreenCapture

    capture = ScreenCapture(monitor=0)
    res = capture.resolution

    assert isinstance(res, tuple)
    assert len(res) == 2
    assert res[0] > 0 and res[1] > 0
