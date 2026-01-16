# bb_detector/main.py
import asyncio
import platform
import signal
import time
from pathlib import Path

from .config import Config
from .platform_utils import get_platform, check_macos_permissions, open_macos_permissions
from .capture import ScreenCapture
from .detector import DeathDetector
from .websocket_client import BBWebSocket
from .overlay import Overlay
from .tray import TrayIcon
from .hotkeys import GlobalHotkeys


class BBDetectorApp:
    def __init__(self):
        self.config = Config()
        self.running = False

        # Components
        self.capture: ScreenCapture | None = None
        self.detector: DeathDetector | None = None
        self.ws: BBWebSocket | None = None
        self.overlay: Overlay | None = None
        self.tray: TrayIcon | None = None
        self.hotkeys: GlobalHotkeys | None = None

        # State
        self.detection_enabled = True
        self.boss_mode = False
        self.connected = False
        self.deaths = 0
        self.boss_deaths = 0
        self.last_death_time = 0

        # Async
        self.loop: asyncio.AbstractEventLoop | None = None

    def run(self):
        print("BB Death Detector starting...")

        # Check macOS permissions
        if get_platform() == 'macos':
            perms = check_macos_permissions()
            if not perms['screen'] or not perms['accessibility']:
                print("macOS permissions required!")
                print("Please enable Screen Recording and Accessibility")
                open_macos_permissions()
                return

        # Load config
        self.config.load()

        # Get profile from config or prompt
        profile = self.config.get('profile.name')
        password = self.config.get('profile.password')

        if not profile:
            profile = input("Enter profile name: ").strip()
            password = input("Enter password: ").strip()
            self.config.set('profile.name', profile)
            self.config.set('profile.password', password)
            self.config.save()

        # Initialize components
        self._init_components(profile, password)

        # Start
        self.running = True
        self._start()

    def _init_components(self, profile: str, password: str):
        monitor = self.config.get('detection.monitor', 0)
        fps = self.config.get('detection.fps', 10)

        self.capture = ScreenCapture(monitor=monitor, fps=fps)
        self.detector = DeathDetector(self.config)

        self.ws = BBWebSocket(
            profile=profile,
            password=password,
            on_state=self._on_ws_state,
            on_connect=self._on_ws_connect,
            on_disconnect=self._on_ws_disconnect
        )

        self.overlay = Overlay(self.config)

        self.tray = TrayIcon(
            on_quit=self._on_quit,
            on_settings=lambda: None,  # TODO
            on_toggle_overlay=self._on_toggle_overlay,
            on_toggle_detection=self._on_toggle_detection
        )

        self.hotkeys = GlobalHotkeys()
        self._register_hotkeys()

    def _register_hotkeys(self):
        hotkeys_cfg = self.config.get('hotkeys', {})

        self.hotkeys.register(
            hotkeys_cfg.get('manual_death', 'ctrl+shift+d'),
            self._on_manual_death
        )
        self.hotkeys.register(
            hotkeys_cfg.get('toggle_boss', 'ctrl+shift+b'),
            self._on_toggle_boss
        )
        self.hotkeys.register(
            hotkeys_cfg.get('toggle_detection', 'ctrl+shift+p'),
            self._on_toggle_detection
        )
        self.hotkeys.register(
            hotkeys_cfg.get('show_overlay', 'ctrl+shift+o'),
            self._on_toggle_overlay
        )

    def _start(self):
        # Setup signal handlers
        signal.signal(signal.SIGINT, lambda s, f: self._on_quit())
        signal.signal(signal.SIGTERM, lambda s, f: self._on_quit())

        # Start tray
        self.tray.start()

        # Start hotkeys
        self.hotkeys.start()

        # Start capture
        self.capture.start()

        # Initialize overlay
        self.overlay.init()

        # Run async loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            self.loop.run_until_complete(self._main_loop())
        except KeyboardInterrupt:
            pass
        finally:
            self._shutdown()

    async def _main_loop(self):
        # Start WebSocket connection
        ws_task = asyncio.create_task(self.ws.connect())

        fps = self.config.get('detection.fps', 10)
        interval = 1.0 / fps
        cooldown = self.config.get('detection.death_cooldown', 5.0)

        while self.running and self.overlay.is_running():
            loop_start = time.time()

            # Detection
            if self.detection_enabled and self.connected:
                frame = self.capture.grab()

                if frame is not None:
                    is_dead, confidence = self.detector.check_death(frame)

                    if is_dead:
                        now = time.time()
                        if now - self.last_death_time > cooldown:
                            self.last_death_time = now
                            await self._handle_death()

            # Update overlay
            self.overlay.update({
                'deaths': self.deaths,
                'boss_mode': self.boss_mode,
                'boss_deaths': self.boss_deaths,
                'connected': self.connected,
                'detection_enabled': self.detection_enabled
            })
            self.overlay.render()

            # FPS limiting
            elapsed = time.time() - loop_start
            await asyncio.sleep(max(0, interval - elapsed))

        ws_task.cancel()

    async def _handle_death(self):
        print("[Detector] Death detected!")

        if self.boss_mode:
            await self.ws.send_boss_death()
        else:
            await self.ws.send_death()

        self.overlay.flash_death()
        self.tray.notify("Death!", "BB")

    # === WebSocket callbacks ===

    def _on_ws_state(self, state: dict):
        self.deaths = state.get('deaths', 0)
        self.boss_mode = state.get('bossFightMode', False)
        self.boss_deaths = state.get('bossDeaths', 0)

    def _on_ws_connect(self):
        self.connected = True
        self.tray.set_connected(True)
        print("[WS] Connected")

    def _on_ws_disconnect(self):
        self.connected = False
        self.tray.set_connected(False)
        print("[WS] Disconnected")

    # === Hotkey callbacks ===

    def _on_manual_death(self):
        if not self.connected or not self.loop:
            return

        asyncio.run_coroutine_threadsafe(
            self.ws.send_boss_death() if self.boss_mode else self.ws.send_death(),
            self.loop
        )
        self.overlay.flash_death()

    def _on_toggle_boss(self):
        if not self.connected or not self.loop:
            return

        if self.boss_mode:
            asyncio.run_coroutine_threadsafe(self.ws.boss_cancel(), self.loop)
        else:
            asyncio.run_coroutine_threadsafe(self.ws.boss_start(), self.loop)

    def _on_toggle_detection(self):
        self.detection_enabled = not self.detection_enabled
        status = "ON" if self.detection_enabled else "OFF"
        self.tray.notify(f"Detection {status}", "BB")
        print(f"[App] Detection: {status}")

    def _on_toggle_overlay(self):
        self.overlay.toggle_visibility()

    def _on_quit(self):
        print("[App] Quit")
        self.running = False

    def _shutdown(self):
        print("[App] Shutting down...")

        self.hotkeys.stop()
        self.capture.stop()

        if self.loop and self.ws:
            self.loop.run_until_complete(self.ws.disconnect())

        self.overlay.destroy()
        self.tray.stop()
        self.config.save()

        print("[App] Goodbye!")


def main():
    app = BBDetectorApp()
    app.run()


if __name__ == '__main__':
    main()
