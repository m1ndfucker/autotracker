# bb_detector/state.py
from typing import Any, Callable, Dict, List
from dataclasses import dataclass


@dataclass
class Milestone:
    """A milestone/checkpoint in the game."""
    id: str
    name: str
    timestamp: int  # ms from session start
    icon: str
    created_at: str  # ISO 8601


@dataclass
class DeathTimestamp:
    """Record of when a death occurred."""
    timestamp: int  # ms from session start
    death_number: int  # counter value at time of death
    created_at: str = ""  # ISO 8601 real-world timestamp


@dataclass
class BossFight:
    """Record of a boss fight."""
    id: str
    name: str
    duration: int  # ms
    deaths_on_boss: int
    deaths_total_before: int
    start_time: int
    end_time: int
    created_at: str


@dataclass
class CharacterStats:
    """Character stats snapshot."""
    id: str
    timestamp: int  # ms from session start
    level: int
    vitality: int
    endurance: int
    strength: int
    skill: int
    bloodtinge: int
    arcane: int
    blood_echoes: int
    insight: int
    notes: str
    created_at: str


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
            # Extended state for milestones and history
            'milestones': [],  # List[Milestone]
            'death_timestamps': [],  # List[DeathTimestamp]
            'boss_fights': [],  # List[BossFight]
            'character_stats': [],  # List[CharacterStats]
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

        # Parse milestones
        if 'milestones' in data:
            milestones = []
            for m in data.get('milestones', []):
                milestones.append(Milestone(
                    id=m.get('id', ''),
                    name=m.get('name', ''),
                    timestamp=m.get('timestamp', 0),
                    icon=m.get('icon', '★'),
                    created_at=m.get('createdAt', '')
                ))
            self._state['milestones'] = milestones
            self._notify('milestones', milestones)

        # Parse death timestamps
        if 'deathTimestamps' in data:
            death_timestamps = []
            for d in data.get('deathTimestamps', []):
                death_timestamps.append(DeathTimestamp(
                    timestamp=d.get('timestamp', 0),
                    death_number=d.get('deathNumber', 0),
                    created_at=d.get('createdAt', '')
                ))
            self._state['death_timestamps'] = death_timestamps
            self._notify('death_timestamps', death_timestamps)

        # Parse boss fights
        if 'bossFights' in data:
            boss_fights = []
            for b in data.get('bossFights', []):
                boss_fights.append(BossFight(
                    id=b.get('id', ''),
                    name=b.get('name', ''),
                    duration=b.get('duration', 0),
                    deaths_on_boss=b.get('deathsOnBoss', 0),
                    deaths_total_before=b.get('deathsTotalBefore', 0),
                    start_time=b.get('startTime', 0),
                    end_time=b.get('endTime', 0),
                    created_at=b.get('createdAt', '')
                ))
            self._state['boss_fights'] = boss_fights
            self._notify('boss_fights', boss_fights)

        # Parse character stats
        if 'characterStats' in data:
            character_stats = []
            for s in data.get('characterStats', []):
                character_stats.append(CharacterStats(
                    id=s.get('id', ''),
                    timestamp=s.get('timestamp', 0),
                    level=s.get('level', 0),
                    vitality=s.get('vitality', 0),
                    endurance=s.get('endurance', 0),
                    strength=s.get('strength', 0),
                    skill=s.get('skill', 0),
                    bloodtinge=s.get('bloodtinge', 0),
                    arcane=s.get('arcane', 0),
                    blood_echoes=s.get('bloodEchoes', 0),
                    insight=s.get('insight', 0),
                    notes=s.get('notes', ''),
                    created_at=s.get('createdAt', '')
                ))
            self._state['character_stats'] = character_stats
            self._notify('character_stats', character_stats)

    def to_dict(self) -> Dict[str, Any]:
        return self._state.copy()
