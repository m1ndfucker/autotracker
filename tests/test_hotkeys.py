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

def test_hotkeys_unregister():
    """unregister removes the hotkey"""
    from bb_detector.hotkeys import GlobalHotkeys

    hotkeys = GlobalHotkeys()
    hotkeys.register('ctrl+shift+x', lambda: None)

    assert frozenset(['ctrl', 'shift', 'x']) in hotkeys.hotkeys

    hotkeys.unregister('ctrl+shift+x')

    assert frozenset(['ctrl', 'shift', 'x']) not in hotkeys.hotkeys

def test_hotkeys_start_stop():
    """start and stop control the listener"""
    from bb_detector.hotkeys import GlobalHotkeys

    hotkeys = GlobalHotkeys()

    assert hotkeys.listener is None

    hotkeys.start()
    assert hotkeys.listener is not None

    hotkeys.stop()
    assert hotkeys.listener is None

def test_hotkeys_callback_execution():
    """Registered callback is stored correctly"""
    from bb_detector.hotkeys import GlobalHotkeys

    hotkeys = GlobalHotkeys()
    test_value = []

    def my_callback():
        test_value.append(1)

    hotkeys.register('ctrl+a', my_callback)

    # Verify callback is stored
    key_set = frozenset(['ctrl', 'a'])
    assert key_set in hotkeys.hotkeys

    # Call the stored callback directly
    hotkeys.hotkeys[key_set]()
    assert test_value == [1]
