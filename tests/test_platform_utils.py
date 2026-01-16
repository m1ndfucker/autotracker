# tests/test_platform_utils.py
import pytest
import platform

def test_get_platform():
    """get_platform returns current platform"""
    from bb_detector.platform_utils import get_platform

    result = get_platform()
    assert result in ['windows', 'macos', 'linux']

def test_get_scale_factor():
    """get_scale_factor returns a positive number"""
    from bb_detector.platform_utils import get_scale_factor

    result = get_scale_factor()
    assert isinstance(result, float)
    assert result >= 1.0
