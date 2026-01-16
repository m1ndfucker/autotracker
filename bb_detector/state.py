# bb_detector/state.py
from typing import Any, Callable, Dict, List


class StateManager:
    """Centralized state management with subscriber notifications."""

    def __init__(self):
        self._state: Dict[str, Any] = {
            'deaths': 0,
            'elapsed': 0,
            'is_running': False,
            'boss_mode': False,
            'boss_deaths': 0,
            'boss_paused': False,
            'connected': False,
            'can_edit': False,
            'detection_enabled': True,
            'profile': None,
            'profile_display_name': None,
        }
        self._subscribers: List[Callable[[str, Any], None]] = []

    def __getattr__(self, name: str) -> Any:
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        if name in self._state:
            return self._state[name]
        raise AttributeError(f"State has no attribute '{name}'")

    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        if key in self._state:
            old_value = self._state[key]
            if old_value != value:
                self._state[key] = value
                self._notify(key, value)

    def subscribe(self, callback: Callable[[str, Any], None]) -> None:
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[str, Any], None]) -> None:
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def _notify(self, key: str, value: Any) -> None:
        for callback in self._subscribers:
            try:
                callback(key, value)
            except Exception as e:
                print(f"[State] Subscriber error for {key}: {e}", flush=True)

    def update_from_server(self, data: Dict[str, Any]) -> None:
        """Update state from server bb-state message."""
        mapping = {
            'deaths': 'deaths',
            'elapsed': 'elapsed',
            'isRunning': 'is_running',
            'bossFightMode': 'boss_mode',
            'bossDeaths': 'boss_deaths',
            'bossPaused': 'boss_paused',
            'canEdit': 'can_edit',
            'profileName': 'profile',
            'displayName': 'profile_display_name',
        }

        for server_key, local_key in mapping.items():
            if server_key in data:
                self.set(local_key, data[server_key])

    def to_dict(self) -> Dict[str, Any]:
        return self._state.copy()
