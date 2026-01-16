# tests/test_config.py
import pytest
import json
import tempfile
from pathlib import Path

def test_config_load_default():
    """Config returns defaults when file doesn't exist"""
    from bb_detector.config import Config

    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config(Path(tmpdir) / "config.json")

        assert config.get('detection.fps') == 10
        assert config.get('detection.death_threshold') == 0.75
        assert config.get('overlay.enabled') == True

def test_config_set_and_get():
    """Config can set and get nested values"""
    from bb_detector.config import Config

    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config(Path(tmpdir) / "config.json")

        config.set('profile.name', 'testuser')
        assert config.get('profile.name') == 'testuser'

def test_config_save_and_load():
    """Config persists to file"""
    from bb_detector.config import Config

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "config.json"

        config1 = Config(path)
        config1.set('profile.name', 'saved_user')
        config1.save()

        config2 = Config(path)
        config2.load()
        assert config2.get('profile.name') == 'saved_user'
