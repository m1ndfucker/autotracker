# bb_detector/config.py
import json
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = {
    "profile": {
        "name": None,
        "password": None,
        "auto_connect": True
    },
    "detection": {
        "fps": 10,
        "death_cooldown": 5.0,
        "death_threshold": 0.75,
        "monitor": 0
    },
    "templates": {
        "death": {
            "builtin": "you_died_en.png",
            "custom": None
        }
    },
    "hotkeys": {
        "manual_death": "ctrl+shift+d",
        "toggle_boss": "ctrl+shift+b",
        "toggle_detection": "ctrl+shift+p",
        "show_overlay": "ctrl+shift+o"
    },
    "overlay": {
        "enabled": True,
        "position": [50, 50],
        "opacity": 0.85,
        "scale": 1.0
    },
    "calibration": {
        "completed": False,
        "death_region": None
    }
}


class Config:
    def __init__(self, path: Path | str | None = None):
        if path is None:
            path = Path.home() / ".bb-detector" / "config.json"
        self.path = Path(path)
        self._data = self._deep_copy(DEFAULT_CONFIG)

    def _deep_copy(self, obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(v) for v in obj]
        return obj

    def load(self) -> bool:
        if not self.path.exists():
            return False

        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            self._merge(self._data, loaded)
            return True
        except (json.JSONDecodeError, IOError):
            return False

    def _merge(self, base: dict, updates: dict):
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge(base[key], value)
            else:
                base[key] = value

    def save(self) -> bool:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self._data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value if value is not None else default

    def set(self, key: str, value: Any):
        keys = key.split('.')
        data = self._data

        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]

        data[keys[-1]] = value
