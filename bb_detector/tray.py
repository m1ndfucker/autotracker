# bb_detector/tray.py
import threading
from typing import Callable, Optional
from PIL import Image, ImageDraw
import pystray


class TrayIcon:
    def __init__(
        self,
        on_quit: Callable,
        on_settings: Callable,
        on_toggle_overlay: Callable,
        on_toggle_detection: Callable
    ):
        self.on_quit = on_quit
        self.on_settings = on_settings
        self.on_toggle_overlay = on_toggle_overlay
        self.on_toggle_detection = on_toggle_detection

        self._connected = False
        self._detection_enabled = True
        self._icon: Optional[pystray.Icon] = None
        self._thread: Optional[threading.Thread] = None

    def _create_icon_image(self, connected: bool) -> Image.Image:
        size = 64
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw skull-like circle
        color = (0, 200, 0, 255) if connected else (200, 0, 0, 255)
        draw.ellipse([4, 4, size-4, size-4], fill=color)

        # Draw "BB" text
        draw.text((size//4, size//4), "BB", fill=(255, 255, 255, 255))

        return img

    def _create_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem(
                'Toggle Detection',
                self._on_toggle_detection,
                checked=lambda item: self._detection_enabled
            ),
            pystray.MenuItem('Toggle Overlay', self._on_toggle_overlay),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Settings', self._on_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Quit', self._on_quit_click)
        )

    def _on_toggle_detection(self, icon, item):
        self._detection_enabled = not self._detection_enabled
        self.on_toggle_detection()

    def _on_toggle_overlay(self, icon, item):
        self.on_toggle_overlay()

    def _on_settings(self, icon, item):
        self.on_settings()

    def _on_quit_click(self, icon, item):
        self._icon.stop()
        self.on_quit()

    def run(self):
        self._icon = pystray.Icon(
            'BB Detector',
            self._create_icon_image(self._connected),
            'BB Death Detector',
            menu=self._create_menu()
        )
        self._icon.run()

    def start(self):
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()

    def stop(self):
        if self._icon:
            self._icon.stop()

    def set_connected(self, connected: bool):
        self._connected = connected
        if self._icon:
            self._icon.icon = self._create_icon_image(connected)

    def notify(self, message: str, title: str = "BB Detector"):
        if self._icon:
            self._icon.notify(message, title)
