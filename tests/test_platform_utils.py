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


from unittest.mock import patch, MagicMock

def test_check_macos_permissions_non_macos():
    """check_macos_permissions returns True on non-macOS"""
    from bb_detector.platform_utils import check_macos_permissions

    with patch('bb_detector.platform_utils.get_platform', return_value='windows'):
        result = check_macos_permissions()
        assert result == {'screen': True, 'accessibility': True}

def test_open_macos_permissions_non_macos():
    """open_macos_permissions does nothing on non-macOS"""
    from bb_detector.platform_utils import open_macos_permissions

    with patch('bb_detector.platform_utils.get_platform', return_value='windows'):
        with patch('subprocess.run') as mock_run:
            open_macos_permissions()
            mock_run.assert_not_called()

def test_open_macos_permissions_macos():
    """open_macos_permissions calls subprocess on macOS"""
    from bb_detector.platform_utils import open_macos_permissions

    with patch('bb_detector.platform_utils.get_platform', return_value='macos'):
        with patch('subprocess.run') as mock_run:
            open_macos_permissions()
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert 'open' in args
            assert 'systempreferences' in args[1]
