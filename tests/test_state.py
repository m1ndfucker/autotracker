# tests/test_state.py
import pytest


def test_state_manager_init():
    """State manager initializes with defaults"""
    from bb_detector.state import StateManager

    state = StateManager()

    assert state.deaths == 0
    assert state.elapsed == 0
    assert state.is_running == False
    assert state.boss_mode == False
    assert state.connected == False


def test_state_manager_subscribe():
    """State manager notifies subscribers on change"""
    from bb_detector.state import StateManager

    state = StateManager()
    notifications = []

    state.subscribe(lambda key, val: notifications.append((key, val)))
    state.set('deaths', 42)

    assert state.deaths == 42
    assert ('deaths', 42) in notifications


def test_state_manager_update_from_server():
    """State manager updates from server state dict"""
    from bb_detector.state import StateManager

    state = StateManager()
    state.update_from_server({
        'deaths': 10,
        'elapsed': 5000,
        'isRunning': True,
        'bossFightMode': True,
        'bossDeaths': 2,
        'canEdit': True
    })

    assert state.deaths == 10
    assert state.elapsed == 5000
    assert state.is_running == True
    assert state.boss_mode == True
    assert state.boss_deaths == 2
    assert state.can_edit == True
