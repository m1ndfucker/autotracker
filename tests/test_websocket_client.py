# tests/test_websocket_client.py
import pytest

def test_websocket_client_init():
    """WebSocket client initializes with profile"""
    from bb_detector.websocket_client import BBWebSocket

    ws = BBWebSocket(
        profile='testprofile',
        password='testpass',
        on_state=lambda s: None,
        on_connect=lambda: None,
        on_disconnect=lambda: None
    )

    assert ws.profile == 'testprofile'
    assert ws.authenticated == False
    assert 'testprofile' in ws.url

def test_websocket_message_builders():
    """Message builder methods return correct format"""
    from bb_detector.websocket_client import BBWebSocket

    ws = BBWebSocket('test', 'pass', lambda s: None, lambda: None, lambda: None)

    death_msg = ws._build_message('bb-death')
    assert death_msg == '{"type": "bb-death"}'

    victory_msg = ws._build_message('bb-boss-victory', name='Test Boss')
    assert '"type": "bb-boss-victory"' in victory_msg
    assert '"name": "Test Boss"' in victory_msg
