# bb_detector/websocket_client.py
import asyncio
import json
from typing import Callable, Optional, Dict, Any

import websockets
from websockets.exceptions import ConnectionClosed


class BBWebSocket:
    WS_URL = "wss://watch.home.kg/ws"

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
                    await self._handle_connection()
            except ConnectionClosed:
                pass
            except Exception as e:
                print(f"[WS] Connection error: {e}")

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
            # Auto-auth if we have password and no edit rights
            if not data.get('canEdit') and self.password and not self.authenticated:
                await self._auth()

            if data.get('canEdit'):
                self.authenticated = True

            self.on_state(data)

        elif msg_type == 'bb-auth-result':
            self.authenticated = data.get('success', False)
            if self.authenticated:
                print("[WS] Authenticated successfully")
            else:
                print(f"[WS] Auth failed: {data.get('error')}")

    async def _auth(self):
        if self.ws:
            msg = self._build_message('bb-auth', password=self.password)
            await self.ws.send(msg)

    async def _send(self, msg_type: str, **kwargs):
        if self.ws and self.authenticated:
            msg = self._build_message(msg_type, **kwargs)
            await self.ws.send(msg)

    async def send_death(self):
        await self._send('bb-death')

    async def send_boss_death(self):
        await self._send('bb-boss-death')

    async def boss_start(self):
        await self._send('bb-boss-start')

    async def boss_pause(self):
        await self._send('bb-boss-pause')

    async def boss_resume(self):
        await self._send('bb-boss-resume')

    async def boss_victory(self, name: str):
        await self._send('bb-boss-victory', name=name)

    async def boss_cancel(self):
        await self._send('bb-boss-cancel')

    async def disconnect(self):
        self._running = False
        if self.ws:
            await self.ws.close()
            self.ws = None
