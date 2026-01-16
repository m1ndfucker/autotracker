# bb_detector/main.py
"""BB Death Detector - Main application entry point."""
import asyncio
import signal
import time

from .config import Config
from .state import StateManager
from .platform_utils import get_platform, check_macos_permissions, open_macos_permissions
from .capture import ScreenCapture
from .detector import DeathDetector
from .websocket_client import BBWebSocket
from .hotkeys import GlobalHotkeys
from .ui.app import App


class BBDetectorApp:
    """Main application controller."""

    def __init__(self):
        self.config = Config()
        self.state = StateManager()
        self.running = False

        # Components
        self.capture: ScreenCapture | None = None
        self.detector: DeathDetector | None = None
        self.ws: BBWebSocket | None = None
        self.hotkeys: GlobalHotkeys | None = None
        self.app: App | None = None

        # Async
        self.loop: asyncio.AbstractEventLoop | None = None
        self._last_death_time = 0

    def run(self):
        """Main entry point."""
        print("BB Death Detector starting...", flush=True)

        # Check macOS permissions
        if get_platform() == 'macos':
            perms = check_macos_permissions()
            if not perms['screen'] or not perms['accessibility']:
                print("macOS permissions required!", flush=True)
                open_macos_permissions()
                return

        # Load config
        self.config.load()

        # Initialize components
        self._init_components()

        # Start
        self.running = True
        self._start()

    def _init_components(self):
        """Initialize all components."""
        monitor = self.config.get('detection.monitor', 0)
        fps = self.config.get('detection.fps', 10)

        self.capture = ScreenCapture(monitor=monitor, fps=fps)
        self.detector = DeathDetector(self.config)

        profile = self.config.get('profile.name')
        password = self.config.get('profile.password') or ''

        self.ws = BBWebSocket(
            profile=profile or 'default',
            password=password,
            on_state=self._on_ws_state,
            on_connect=self._on_ws_connect,
            on_disconnect=self._on_ws_disconnect
        )

        self.hotkeys = GlobalHotkeys()

        # Create UI
        self.app = App(
            config=self.config,
            state=self.state,
            on_manual_death=self._on_manual_death,
            on_timer_start=self._on_timer_start,
            on_timer_stop=self._on_timer_stop,
            on_timer_reset=self._on_timer_reset,
            on_boss_start=self._on_boss_start,
            on_boss_victory=self._on_boss_victory,
            on_boss_cancel=self._on_boss_cancel,
            on_toggle_detection=self._on_toggle_detection,
            on_profile_select=self._on_profile_select,
            on_template_change=self._on_template_change,
            on_capture=self._on_capture,
            on_test_detection=self._on_test_detection,
            on_quit=self._on_quit,
        )

    def _register_hotkeys(self):
        """Register global hotkeys."""
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
            self._on_toggle_mode
        )

    def _start(self):
        """Start all services and main loop."""
        # Setup signal handlers
        signal.signal(signal.SIGINT, lambda s, f: self._on_quit())
        signal.signal(signal.SIGTERM, lambda s, f: self._on_quit())

        # Initialize UI
        self.app.init()

        # Register hotkeys
        self._register_hotkeys()
        self.hotkeys.start()

        # Start capture
        self.capture.start()

        # Show profile dialog if no profile configured
        if not self.config.get('profile.name'):
            self.app.show_profile_dialog()

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
        """Main application loop."""
        # Start WebSocket if profile configured
        if self.config.get('profile.name'):
            ws_task = asyncio.create_task(self.ws.connect())
        else:
            ws_task = None

        fps = self.config.get('detection.fps', 10)
        interval = 1.0 / fps
        cooldown = self.config.get('detection.death_cooldown', 5.0)

        while self.running and self.app.is_running():
            loop_start = time.time()

            # Detection
            if self.state.detection_enabled and self.state.connected:
                frame = self.capture.grab()

                if frame is not None:
                    is_dead, confidence = self.detector.check_death(frame)

                    if is_dead:
                        now = time.time()
                        if now - self._last_death_time > cooldown:
                            self._last_death_time = now
                            await self._handle_death()

            # Update UI state (timer elapsed if running)
            if self.state.is_running:
                # Timer is managed by server, we just display
                pass

            # Render UI
            self.app.render()

            # FPS limiting
            elapsed = time.time() - loop_start
            await asyncio.sleep(max(0, interval - elapsed))

        if ws_task:
            ws_task.cancel()

    async def _handle_death(self):
        """Handle detected death."""
        print("[Detector] Death detected!", flush=True)

        if self.state.boss_mode:
            await self.ws.send_boss_death()
        else:
            await self.ws.send_death()

    # === WebSocket callbacks ===

    def _on_ws_state(self, data: dict):
        """Handle server state update."""
        self.state.update_from_server(data)
        self.state.set('connected', True)

    def _on_ws_connect(self):
        """Handle WebSocket connect."""
        self.state.set('connected', True)
        print("[WS] Connected", flush=True)

    def _on_ws_disconnect(self):
        """Handle WebSocket disconnect."""
        self.state.set('connected', False)
        self.state.set('can_edit', False)
        print("[WS] Disconnected", flush=True)

    # === UI Callbacks ===

    def _on_manual_death(self):
        """Handle manual death button/hotkey."""
        if not self.state.connected or not self.loop:
            return

        asyncio.run_coroutine_threadsafe(
            self.ws.send_boss_death() if self.state.boss_mode else self.ws.send_death(),
            self.loop
        )

    def _on_timer_start(self):
        """Handle timer start."""
        if self.loop and self.state.connected:
            asyncio.run_coroutine_threadsafe(self.ws.start_timer(), self.loop)

    def _on_timer_stop(self):
        """Handle timer stop."""
        if self.loop and self.state.connected:
            asyncio.run_coroutine_threadsafe(self.ws.stop_timer(), self.loop)

    def _on_timer_reset(self):
        """Handle timer reset."""
        if self.loop and self.state.connected:
            asyncio.run_coroutine_threadsafe(self.ws.reset(), self.loop)

    def _on_boss_start(self):
        """Handle boss start."""
        if self.loop and self.state.connected:
            asyncio.run_coroutine_threadsafe(self.ws.boss_start(), self.loop)

    def _on_boss_victory(self, name: str):
        """Handle boss victory."""
        if self.loop and self.state.connected:
            asyncio.run_coroutine_threadsafe(self.ws.boss_victory(name), self.loop)

    def _on_boss_cancel(self):
        """Handle boss cancel."""
        if self.loop and self.state.connected:
            asyncio.run_coroutine_threadsafe(self.ws.boss_cancel(), self.loop)

    def _on_toggle_boss(self):
        """Toggle boss mode (hotkey)."""
        if self.state.boss_mode:
            self._on_boss_cancel()
        else:
            self._on_boss_start()

    def _on_toggle_detection(self):
        """Toggle detection on/off."""
        self.state.set('detection_enabled', not self.state.detection_enabled)
        status = "ON" if self.state.detection_enabled else "OFF"
        print(f"[App] Detection: {status}", flush=True)

    def _on_toggle_mode(self):
        """Toggle compact/full mode."""
        if self.app:
            self.app.toggle_mode()

    def _on_profile_select(self, name: str, password: str, is_new: bool):
        """Handle profile selection."""
        if is_new:
            # Create profile via API
            import requests
            try:
                resp = requests.post(
                    'https://watch.home.kg/api/bb-profiles',
                    json={'name': name, 'password': password},
                    timeout=5
                )
                if not resp.ok:
                    print(f"[App] Failed to create profile: {resp.text}", flush=True)
                    return
            except Exception as e:
                print(f"[App] Failed to create profile: {e}", flush=True)
                return

        # Save to config
        self.config.set('profile.name', name)
        self.config.set('profile.password', password)
        self.config.save()

        # Reconnect WebSocket with new profile
        if self.ws and self.loop:
            asyncio.run_coroutine_threadsafe(self.ws.disconnect(), self.loop)

        self.ws = BBWebSocket(
            profile=name,
            password=password,
            on_state=self._on_ws_state,
            on_connect=self._on_ws_connect,
            on_disconnect=self._on_ws_disconnect
        )

        if self.loop:
            asyncio.run_coroutine_threadsafe(self.ws.connect(), self.loop)

    def _on_template_change(self, template: str):
        """Handle template change."""
        self.config.set('templates.death.builtin', template)
        self.config.save()
        self.detector.reload(self.config)

    def _on_capture(self):
        """Capture current screen for calibration."""
        return self.capture.grab()

    def _on_test_detection(self, frame):
        """Test detection on frame."""
        return self.detector.check_death(frame)

    def _on_quit(self):
        """Handle quit."""
        print("[App] Quit", flush=True)
        self.running = False

    def _shutdown(self):
        """Cleanup and shutdown."""
        print("[App] Shutting down...", flush=True)

        if self.hotkeys:
            self.hotkeys.stop()

        if self.capture:
            self.capture.stop()

        if self.loop and self.ws:
            self.loop.run_until_complete(self.ws.disconnect())

        if self.app:
            self.app.destroy()

        self.config.save()

        print("[App] Goodbye!", flush=True)


def main():
    app = BBDetectorApp()
    app.run()


if __name__ == '__main__':
    main()
