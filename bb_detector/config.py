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
    "settings": {
        "tick_seconds": 0.3,
        "debug_every_ticks": 30,
        "consecutive_hits": 2,
        "cooldown_seconds": 5.0,
        "monitor_index": 0,
        "fuzzy_ocr_matching": True
    },
    "games": {
        "Bloodborne": {
            "region": {
                "use_percentages": True,
                "window_name": None,
                "left": 0.30,
                "top": 0.40,
                "width": 0.40,
                "height": 0.20
            },
            "keywords": [
                "YOUDIED", "YOU DIED", "YOUDIE",
                "Y0UDIED", "Y0U DIED", "Y0UDIE",
                "YOUD1ED", "YOUD13D", "Y0UD13D",
                "YOU D13D", "Y0U D13D",
                "ТЫМЕРТВ", "ТЫ МЕРТВ"
            ],
            "tesseract_config": "--oem 3 --psm 6",
            "process_names": ["rpcs3.exe", "rpcs3", "VLC", "vlc"]
        },
        "Dark Souls 3": {
            "region": {
                "use_percentages": True,
                "window_name": None,
                "left": 0.2708,
                "top": 0.4352,
                "width": 0.4583,
                "height": 0.1852
            },
            "keywords": [
                "YOUDIED", "YOUDIE", "YOUD1ED", "YOUDlED",
                "YOUDI", "OUDIED", "YOUDIE0",
                "Y0UDIED", "Y0UDIE", "Y0UD1ED", "Y0UD13D",
                "Y0UDI3D", "YOUD13D", "YOUDI3D",
                "Y0U DIED", "YOU D13D", "Y0U D13D",
                "1OUDIED", "10UDIED", "YOUD1E0", "Y0UD1E0"
            ],
            "tesseract_config": "--oem 3 --psm 7 -c tessedit_char_whitelist=YOUDIEADFT",
            "process_names": ["darksoulsiii.exe", "dark souls iii.exe"]
        },
        "Dark Souls Remastered": {
            "region": {
                "use_percentages": True,
                "window_name": None,
                "left": 0.2708,
                "top": 0.4352,
                "width": 0.4583,
                "height": 0.1852
            },
            "keywords": [
                "YOUDIED", "YOUDIE", "YOUD1ED", "YOUDlED",
                "YOUDI", "OUDIED", "YOUDIE0",
                "Y0UDIED", "Y0UDIE", "Y0UD1ED", "Y0UD13D",
                "Y0UDI3D", "YOUD13D", "YOUDI3D",
                "Y0U DIED", "YOU D13D", "Y0U D13D"
            ],
            "tesseract_config": "--oem 3 --psm 7 -c tessedit_char_whitelist=YOUDIEADFT",
            "process_names": ["darksoulsremastered.exe", "DARK SOULS REMASTERED"]
        },
        "Elden Ring": {
            "region": {
                "use_percentages": True,
                "window_name": None,
                "left": 0.2708,
                "top": 0.4352,
                "width": 0.4583,
                "height": 0.1852
            },
            "keywords": [
                "YOUDIED", "YOUDIE", "YOUDED", "DIED",
                "Y0UDIED", "Y0UDIE", "Y0UDED",
                "YOUD13D", "YOUD1ED", "YOUDI3D",
                "Y0UD13D", "Y0UD1ED", "Y0UDI3D",
                "Y0U DIED", "YOU D13D", "Y0U D13D"
            ],
            "tesseract_config": "--oem 3 --psm 7 -c tessedit_char_whitelist=YOUDIEADFT",
            "process_names": ["eldenring.exe", "elden ring.exe"]
        },
        "Sekiro": {
            "region": {
                "use_percentages": True,
                "window_name": None,
                "left": 0.3802,
                "top": 0.2685,
                "width": 0.2240,
                "height": 0.4074
            },
            "keywords": [
                "YOUDIED", "YOUDIE", "DEATH",
                "Y0UDIED", "Y0UDIE",
                "YOUD13D", "YOUD1ED", "Y0UD13D", "Y0UD1ED",
                "D34TH", "DE4TH", "DEA7H",
                "Y0U DIED", "YOU D13D", "Y0U D13D"
            ],
            "tesseract_config": "--oem 3 --psm 7 -c tessedit_char_whitelist=YOUDIEADFT",
            "process_names": ["sekiro.exe"]
        },
        "Custom": {
            "region": {
                "use_percentages": True,
                "window_name": None,
                "left": 0.25,
                "top": 0.40,
                "width": 0.50,
                "height": 0.20
            },
            "keywords": ["YOUDIED", "YOU DIED", "DIED", "DEATH", "GAME OVER"],
            "tesseract_config": "--oem 3 --psm 6",
            "process_names": []
        }
    },
    "current_game": "Bloodborne",
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
