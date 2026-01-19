# bb_detector/websocket_client.py
import asyncio
import json
from typing import Callable, Optional, Dict

import websockets
from websockets.exceptions import ConnectionClosed


class BBWebSocket:
    """WebSocket client for Bloodborne death tracker.

    Server: bloodborne-server.js (multi-profile)
    - Endpoint: wss://soulsdeaths.somework.dev/ws?bloodborne=true&profile=PROFILE_NAME
    - Auth: Send bb-auth with password to get canEdit=true
    - Client sends: bb-death, bb-boss-death, bb-start, bb-stop, bb-boss-start, etc.
    - Server sends: bb-state with full state
    """

    WS_URL = "wss://soulsdeaths.somework.dev/ws"

    def __init__(
        self,
        profile: str,
        password: str,
        on_state: Callable[[Dict], None],
        on_connect: Callable[[], None],
        on_disconnect: Callable[[], None]
    ):
        self.profile = profile
        self.password = password
        self.on_state = on_state
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect

        # bloodborne=true routes to bloodborne-server.js via Caddy
        self.url = f"{self.WS_URL}?bloodborne=true&profile={profile}"
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.authenticated = False
        self._running = False
        self._reconnect_delay = 3.0

    def _build_message(self, msg_type: str, **kwargs) -> str:
        data = {'type': msg_type, **kwargs}
        return json.dumps(data)

    async def connect(self):
        self._running = True

        while self._running:
            try:
                async with websockets.connect(self.url) as ws:
                    self.ws = ws
                    self.authenticated = False
                    await self._handle_connection()
            except ConnectionClosed:
                pass
            except Exception as e:
                print(f"[WS] Connection error: {e}", flush=True)

            if self._running:
                self.authenticated = False
                self.on_disconnect()
                await asyncio.sleep(self._reconnect_delay)

    async def _handle_connection(self):
        self.on_connect()

        async for message in self.ws:
            try:
                data = json.loads(message)
                await self._handle_message(data)
            except json.JSONDecodeError:
                pass

    async def _handle_message(self, data: Dict):
        msg_type = data.get('type')

        if msg_type == 'bb-state':
            # Auto-authenticate if we have password and no edit rights yet
            if not data.get('canEdit') and self.password and not self.authenticated:
                await self._auth()

            if data.get('canEdit'):
                self.authenticated = True

            # Pass full state to callback
            self.on_state(data)

        elif msg_type == 'bb-auth-result':
            self.authenticated = data.get('success', False)
            if self.authenticated:
                print("[WS] Authenticated successfully", flush=True)
            else:
                print(f"[WS] Auth failed: {data.get('error')}", flush=True)

        elif msg_type == 'bb-error':
            print(f"[WS] Error: {data.get('error')} ({data.get('code')})", flush=True)

    async def _auth(self):
        """Authenticate with password to get edit permissions."""
        if self.ws and self.password:
            msg = self._build_message('bb-auth', password=self.password)
            await self.ws.send(msg)

    async def _send(self, msg_type: str, **kwargs):
        """Send message to server. Requires authentication for edit commands."""
        if self.ws and self.authenticated:
            msg = self._build_message(msg_type, **kwargs)
            await self.ws.send(msg)

    async def send_death(self):
        """Increment death counter."""
        await self._send('bb-death')

    async def send_boss_death(self):
        """Increment death counter (also increments boss deaths if in boss mode)."""
        await self._send('bb-boss-death')

    async def start_timer(self):
        """Start the timer."""
        await self._send('bb-start')

    async def stop_timer(self):
        """Stop the timer."""
        await self._send('bb-stop')

    async def boss_start(self):
        """Start boss fight mode."""
        await self._send('bb-boss-start')

    async def boss_pause(self):
        """Pause boss fight timer."""
        await self._send('bb-boss-pause')

    async def boss_resume(self):
        """Resume boss fight timer."""
        await self._send('bb-boss-resume')

    async def boss_victory(self, name: str = ""):
        """Record boss victory and end boss fight mode."""
        await self._send('bb-boss-victory', name=name)

    async def boss_cancel(self):
        """Cancel boss fight without recording."""
        await self._send('bb-boss-cancel')

    async def reset(self):
        """Reset all state (deaths, timer, bosses)."""
        await self._send('bb-reset')

    async def set_time(self, elapsed_ms: int):
        """Set elapsed time in milliseconds."""
        await self._send('bb-set-time', elapsed=elapsed_ms)

    async def set_deaths(self, deaths: int):
        """Set death count."""
        await self._send('bb-set-deaths', deaths=deaths)

    # === Milestone Methods ===

    async def add_milestone(self, name: str, icon: str = "★"):
        """Add a new milestone at current time."""
        await self._send('bb-milestone-add', name=name, icon=icon)

    async def edit_milestone(self, id: str, name: str, icon: str, timestamp: int = None):
        """Edit an existing milestone."""
        data = {'id': id, 'name': name, 'icon': icon}
        if timestamp is not None:
            data['timestamp'] = timestamp
        await self._send('bb-milestone-edit', **data)

    async def delete_milestone(self, id: str):
        """Delete a milestone."""
        await self._send('bb-milestone-delete', id=id)

    # === Character Stats Methods ===

    async def add_stats(self, stats: dict):
        """Add character stats snapshot."""
        await self._send('bb-stats-add', **stats)

    async def edit_stats(self, id: str, stats: dict):
        """Edit character stats."""
        await self._send('bb-stats-edit', id=id, **stats)

    async def delete_stats(self, id: str):
        """Delete character stats."""
        await self._send('bb-stats-delete', id=id)

    async def disconnect(self):
        self._running = False
        if self.ws:
            await self.ws.close()
            self.ws = None
