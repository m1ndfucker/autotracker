# tests/test_hotkeys.py
import pytest

def test_hotkeys_register():
    """Hotkeys can register callbacks"""
    from bb_detector.hotkeys import GlobalHotkeys

    hotkeys = GlobalHotkeys()
    callback_called = [False]

    def test_callback():
        callback_called[0] = True

    hotkeys.register('ctrl+shift+t', test_callback)

    assert frozenset(['ctrl', 'shift', 't']) in hotkeys.hotkeys

def test_hotkeys_normalize_macos():
    """cmd normalizes to ctrl"""
    from bb_detector.hotkeys import GlobalHotkeys

    hotkeys = GlobalHotkeys()
    hotkeys.register('cmd+shift+d', lambda: None)

    assert frozenset(['ctrl', 'shift', 'd']) in hotkeys.hotkeys
