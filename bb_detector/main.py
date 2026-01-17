# bb_detector/main.py
"""BB Death Detector - Main application entry point."""
import asyncio
import signal
import time

from .config import Config
from .state import StateManager
from .platform_utils import get_platform, check_macos_permissions, open_macos_permissions, open_macos_accessibility_settings
from .capture import ScreenCapture
from .detector import DeathDetector
from .websocket_client import BBWebSocket
from .hotkeys import GlobalHotkeys
from .window_utils import find_window_by_name, capture_window_region
from .ui.app import App
from .tesseract_utils import configure_pytesseract


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

        # Configure Tesseract OCR (bundled or system)
        configure_pytesseract()

        # Check macOS screen recording permission (required for detection)
        if get_platform() == 'macos':
            perms = check_macos_permissions()
            if not perms['screen']:
                print("Нужно разрешение на Запись экрана!", flush=True)
                print("Добавь Terminal (или VS Code/iTerm) в список и включи.", flush=True)
                print("Путь: Системные настройки > Конфиденциальность и безопасность > Запись экрана", flush=True)
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
            on_capture=self._on_capture,
            on_capture_region=self._on_capture_region,
            on_test_detection=self._on_test_detection,
            on_save_region=self._on_save_region,
            on_quit=self._on_quit,
            on_f9_pressed=self._on_f9_pressed,
            on_add_milestone=self._on_add_milestone,
            on_delete_milestone=self._on_delete_milestone,
            on_add_stats=self._on_add_stats,
            on_delete_stats=self._on_delete_stats,
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
        # F9 for region selection
        self.hotkeys.register('f9', self._on_f9_hotkey)

    def _start(self):
        """Start all services and main loop."""
        # Setup signal handlers
        signal.signal(signal.SIGINT, lambda s, f: self._on_quit())
        signal.signal(signal.SIGTERM, lambda s, f: self._on_quit())

        # Initialize UI
        self.app.init()

        # Register hotkeys (but don't start listener yet)
        self._register_hotkeys()

        # Start capture
        self.capture.start()

        # Show profile dialog if no profile configured
        if not self.config.get('profile.name'):
            self.app.show_profile_dialog()

        # Create async loop BEFORE starting hotkeys (avoids thread conflict on macOS)
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Start hotkeys AFTER asyncio loop is set up
        # Check accessibility permissions first on macOS
        if get_platform() == 'macos':
            perms = check_macos_permissions()
            if not perms['accessibility']:
                print("[!] Нет разрешения на Универсальный доступ!", flush=True)
                print("    Открываю настройки...", flush=True)
                print("    Добавь Terminal в список и включи его.", flush=True)
                print("    Путь: Системные настройки > Конфиденциальность и безопасность > Универсальный доступ", flush=True)
                open_macos_accessibility_settings()

        self.hotkeys.start()

        try:
            self.loop.run_until_complete(self._main_loop())
        except KeyboardInterrupt:
            pass
        finally:
            self._shutdown()

    def _get_detection_region(self) -> tuple[int, int, int, int] | None:
        """
        Get detection region in absolute screen coordinates.

        Supports both:
        - Window-relative regions (with window_name, x_percent, etc.)
        - Absolute regions (with x, y, width, height)

        Returns:
            Tuple of (x, y, width, height) or None if no valid region.
        """
        # Check for window-relative region first
        window_name = self.config.get('detection.region.window_name', '')

        if window_name:
            # Window-relative mode
            window = find_window_by_name(window_name)
            if window:
                wb = window['bounds']
                x_pct = self.config.get('detection.region.x_percent', 0)
                y_pct = self.config.get('detection.region.y_percent', 0)
                w_pct = self.config.get('detection.region.w_percent', 0)
                h_pct = self.config.get('detection.region.h_percent', 0)

                if w_pct > 0 and h_pct > 0:
                    x = int(wb['x'] + x_pct * wb['width'])
                    y = int(wb['y'] + y_pct * wb['height'])
                    w = int(w_pct * wb['width'])
                    h = int(h_pct * wb['height'])
                    return (x, y, w, h)

            # Window not found, try absolute fallback
            abs_x = self.config.get('detection.region.absolute.x', 0)
            abs_y = self.config.get('detection.region.absolute.y', 0)
            abs_w = self.config.get('detection.region.absolute.width', 0)
            abs_h = self.config.get('detection.region.absolute.height', 0)

            if abs_w > 0 and abs_h > 0:
                return (abs_x, abs_y, abs_w, abs_h)

        # Legacy absolute region (backwards compatibility)
        region_x = self.config.get('detection.region.x', 0)
        region_y = self.config.get('detection.region.y', 0)
        region_w = self.config.get('detection.region.width', 0)
        region_h = self.config.get('detection.region.height', 0)

        if region_w > 0 and region_h > 0:
            return (region_x, region_y, region_w, region_h)

        return None

    async def _main_loop(self):
        """Main application loop."""
        # Start WebSocket if profile configured
        if self.config.get('profile.name'):
            ws_task = asyncio.create_task(self.ws.connect())
        else:
            ws_task = None

        # Detection runs at lower FPS, UI renders every frame
        detection_fps = self.config.get('detection.fps', 10)
        detection_interval = 1.0 / detection_fps
        cooldown = self.config.get('detection.death_cooldown', 5.0)

        # UI renders at 60 FPS for smooth experience
        ui_interval = 1.0 / 60.0
        last_detection_time = 0

        # Detection runs in background thread to not block UI
        self._detection_result = None
        self._detection_running = False

        while self.running and self.app.is_running():
            loop_start = time.time()

            # Check detection result from background thread
            if self._detection_result is not None:
                is_dead, confidence = self._detection_result
                self._detection_result = None

                # Debug: show detection status periodically
                if hasattr(self, '_debug_counter'):
                    self._debug_counter += 1
                else:
                    self._debug_counter = 0

                if self._debug_counter % 10 == 0:  # Every second
                    method = self.detector.last_method or "none"
                    print(f"[Debug] Detection: match={is_dead}, conf={confidence:.2f}, method={method}", flush=True)

                if is_dead:
                    now = time.time()
                    if now - self._last_death_time > cooldown:
                        self._last_death_time = now
                        await self._handle_death()

            # Start detection in background thread (if not already running)
            if (time.time() - last_detection_time >= detection_interval and
                not self._detection_running and
                self.state.detection_enabled and self.state.connected):

                last_detection_time = time.time()
                self._detection_running = True

                # Run detection in thread pool to not block UI
                asyncio.get_event_loop().run_in_executor(
                    None,  # Default thread pool
                    self._run_detection_sync
                )

            # Render UI every frame (60 FPS) - never blocked by detection
            self.app.render()

            # FPS limiting for UI
            elapsed = time.time() - loop_start
            await asyncio.sleep(max(0, ui_interval - elapsed))

        if ws_task:
            ws_task.cancel()

    def _run_detection_sync(self):
        """Run detection synchronously in background thread."""
        try:
            frame = None

            # Check for window-relative region (captures only target window)
            window_name = self.config.get('detection.region.window_name', '')
            if window_name:
                x_pct = self.config.get('detection.region.x_percent', 0)
                y_pct = self.config.get('detection.region.y_percent', 0)
                w_pct = self.config.get('detection.region.w_percent', 0)
                h_pct = self.config.get('detection.region.h_percent', 0)

                if w_pct > 0 and h_pct > 0:
                    # Use window-specific capture (ignores windows on top)
                    frame = capture_window_region(window_name, x_pct, y_pct, w_pct, h_pct)

            # Fallback to screen capture
            if frame is None:
                region = self._get_detection_region()
                if region:
                    x, y, w, h = region
                    frame = self.capture.grab_region(x, y, w, h)
                else:
                    frame = self.capture.grab()

            if frame is not None:
                is_dead, confidence = self.detector.check_death(frame)
                self._detection_result = (is_dead, confidence)
            else:
                self._detection_result = (False, 0.0)
        except Exception as e:
            print(f"[Detection] Error: {e}", flush=True)
            self._detection_result = (False, 0.0)
        finally:
            self._detection_running = False

    async def _handle_death(self):
        """Handle detected death."""
        print("[Detector] Death detected!", flush=True)

        if self.state.boss_mode:
            print("[WS] Sending boss death...", flush=True)
            await self.ws.send_boss_death()
        else:
            print("[WS] Sending death...", flush=True)
            await self.ws.send_death()
        print(f"[WS] Sent! Deaths count: {self.state.deaths}", flush=True)

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

    # === Milestone Callbacks ===

    def _on_add_milestone(self, name: str, icon: str):
        """Handle add milestone."""
        if self.loop and self.state.connected:
            asyncio.run_coroutine_threadsafe(
                self.ws.add_milestone(name, icon),
                self.loop
            )

    def _on_delete_milestone(self, milestone_id: str):
        """Handle delete milestone."""
        if self.loop and self.state.connected:
            asyncio.run_coroutine_threadsafe(
                self.ws.delete_milestone(milestone_id),
                self.loop
            )

    # === Stats Callbacks ===

    def _on_add_stats(self, stats: dict):
        """Handle add character stats."""
        if self.loop and self.state.connected:
            asyncio.run_coroutine_threadsafe(
                self.ws.add_stats(stats),
                self.loop
            )

    def _on_delete_stats(self, stats_id: str):
        """Handle delete character stats."""
        if self.loop and self.state.connected:
            asyncio.run_coroutine_threadsafe(
                self.ws.delete_stats(stats_id),
                self.loop
            )

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

    def _on_f9_hotkey(self):
        """Handle F9 hotkey for region selection."""
        if self.app:
            self.app.on_f9_pressed()

    def _on_f9_pressed(self):
        """Callback for UI to check F9 state (not used, kept for compatibility)."""
        pass

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

    def _on_capture(self):
        """Capture current screen for calibration."""
        return self.capture.grab()

    def _on_capture_region(self, region: dict):
        """Capture specific screen region for calibration."""
        # Support window-relative regions - use window-specific capture
        if 'window_name' in region and region.get('w_percent', 0) > 0:
            # Use capture_window_region - captures only target window, ignores windows on top
            frame = capture_window_region(
                region['window_name'],
                region.get('x_percent', 0),
                region.get('y_percent', 0),
                region.get('w_percent', 0),
                region.get('h_percent', 0)
            )
            if frame is not None:
                return frame
            # Fallback to screen capture if window not found

        # Fallback: standard screen capture
        frame = self.capture.grab()
        if frame is None:
            return None

        # Legacy absolute region
        x = region.get('x', 0)
        y = region.get('y', 0)
        w = region.get('width', 0)
        h = region.get('height', 0)

        # If no region specified (all zeros), return full frame
        if w == 0 or h == 0:
            return frame

        # Crop to region
        frame_h, frame_w = frame.shape[:2]
        x = max(0, min(x, frame_w - 1))
        y = max(0, min(y, frame_h - 1))
        w = min(w, frame_w - x)
        h = min(h, frame_h - y)

        return frame[y:y+h, x:x+w]

    def _on_save_region(self, region: dict):
        """Save screen region to config."""
        # Check if this is a window-relative region
        if 'window_name' in region:
            # New window-relative format
            self.config.set('detection.region.window_name', region.get('window_name', ''))
            self.config.set('detection.region.window_title', region.get('window_title', ''))
            self.config.set('detection.region.x_percent', region.get('x_percent', 0))
            self.config.set('detection.region.y_percent', region.get('y_percent', 0))
            self.config.set('detection.region.w_percent', region.get('w_percent', 0))
            self.config.set('detection.region.h_percent', region.get('h_percent', 0))

            # Also save absolute as fallback
            if 'absolute' in region:
                self.config.set('detection.region.absolute.x', region['absolute'].get('x', 0))
                self.config.set('detection.region.absolute.y', region['absolute'].get('y', 0))
                self.config.set('detection.region.absolute.width', region['absolute'].get('width', 0))
                self.config.set('detection.region.absolute.height', region['absolute'].get('height', 0))

            # Clear legacy format
            self.config.set('detection.region.x', 0)
            self.config.set('detection.region.y', 0)
            self.config.set('detection.region.width', 0)
            self.config.set('detection.region.height', 0)
        else:
            # Legacy absolute format
            self.config.set('detection.region.x', region.get('x', 0))
            self.config.set('detection.region.y', region.get('y', 0))
            self.config.set('detection.region.width', region.get('width', 0))
            self.config.set('detection.region.height', region.get('height', 0))

            # Clear window-relative format
            self.config.set('detection.region.window_name', '')

        self.config.save()

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
