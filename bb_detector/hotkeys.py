# bb_detector/hotkeys.py
import threading
from typing import Callable, Dict, Set
from pynput import keyboard


class GlobalHotkeys:
    def __init__(self):
        self.hotkeys: Dict[frozenset, Callable] = {}
        self.current_keys: Set[str] = set()
        self.listener: keyboard.Listener | None = None
        self._lock = threading.Lock()

    def register(self, keys: str, callback: Callable):
        key_set = frozenset(
            k.strip().lower().replace('cmd', 'ctrl')
            for k in keys.split('+')
        )
        self.hotkeys[key_set] = callback

    def unregister(self, keys: str):
        key_set = frozenset(
            k.strip().lower().replace('cmd', 'ctrl')
            for k in keys.split('+')
        )
        self.hotkeys.pop(key_set, None)

    def start(self):
        if self.listener is not None:
            return

        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()

    def stop(self):
        if self.listener:
            self.listener.stop()
            self.listener = None

    def _normalize_key(self, key) -> str | None:
        special_map = {
            keyboard.Key.ctrl_l: 'ctrl',
            keyboard.Key.ctrl_r: 'ctrl',
            keyboard.Key.cmd: 'ctrl',
            keyboard.Key.cmd_l: 'ctrl',
            keyboard.Key.cmd_r: 'ctrl',
            keyboard.Key.shift_l: 'shift',
            keyboard.Key.shift_r: 'shift',
            keyboard.Key.alt_l: 'alt',
            keyboard.Key.alt_r: 'alt',
            keyboard.Key.alt_gr: 'alt',
            keyboard.Key.space: 'space',
            keyboard.Key.enter: 'enter',
            keyboard.Key.esc: 'esc',
            keyboard.Key.tab: 'tab',
            keyboard.Key.backspace: 'backspace',
        }

        if key in special_map:
            return special_map[key]

        if hasattr(key, 'char') and key.char:
            return key.char.lower()

        if hasattr(key, 'name') and key.name:
            return key.name.lower()

        return None

    def _on_press(self, key):
        key_name = self._normalize_key(key)
        if not key_name:
            return

        with self._lock:
            self.current_keys.add(key_name)
            frozen = frozenset(self.current_keys)

            if frozen in self.hotkeys:
                callback = self.hotkeys[frozen]
                threading.Thread(target=callback, daemon=True).start()

    def _on_release(self, key):
        key_name = self._normalize_key(key)
        if key_name:
            with self._lock:
                self.current_keys.discard(key_name)
