# bb_detector/ui/tabs/settings.py
"""Settings tab - configuration options."""
import dearpygui.dearpygui as dpg
from typing import Callable, Dict, Any, List
import mss
from ..theme import COLORS


def _get_monitor_list() -> List[str]:
    """Get list of available monitors."""
    with mss.mss() as sct:
        # mss monitors[0] is "all monitors combined", skip it
        count = len(sct.monitors) - 1
        return [f"Display {i+1}" for i in range(count)]


class SettingsTab:
    """Settings tab with profile, detection, hotkeys, window settings."""

    def __init__(
        self,
        config: Any,
        on_change_profile: Callable[[], None],
        on_save_settings: Callable[[Dict], None],
    ):
        self.config = config
        self.on_change_profile = on_change_profile
        self.on_save_settings = on_save_settings
        self._recording_hotkey: str = None

    def create(self, parent: int):
        """Create the Settings tab content."""
        with dpg.tab(label="Settings", parent=parent):
            dpg.add_spacer(height=10)

            # Profile section
            dpg.add_text("PROFILE", color=COLORS['text_dim'])
            dpg.add_spacer(height=5)

            with dpg.child_window(height=70, border=True):
                dpg.add_spacer(height=5)
                with dpg.group(horizontal=True):
                    dpg.add_text("Current:", color=COLORS['text_dim'])
                    dpg.add_text("Not connected", tag="settings_profile_name")

                with dpg.group(horizontal=True):
                    dpg.add_text("Status:", color=COLORS['text_dim'])
                    dpg.add_text("Disconnected", tag="settings_profile_status", color=COLORS['accent'])

                dpg.add_spacer(height=5)
                dpg.add_button(label="Change Profile", callback=self._on_change_profile)

            dpg.add_spacer(height=15)

            # Detection section
            dpg.add_text("DETECTION", color=COLORS['text_dim'])
            dpg.add_spacer(height=5)

            # Monitor selection
            monitors = _get_monitor_list()
            with dpg.group(horizontal=True):
                dpg.add_text("Monitor:", color=COLORS['text_dim'], indent=10)
                dpg.add_combo(
                    items=monitors if monitors else ["Display 1"],
                    default_value=monitors[0] if monitors else "Display 1",
                    tag="settings_monitor",
                    width=150,
                    callback=self._on_setting_change
                )

            dpg.add_spacer(height=5)

            # FPS
            with dpg.group(horizontal=True):
                dpg.add_text("FPS:", color=COLORS['text_dim'], indent=10)
                dpg.add_combo(
                    items=["5", "10", "15", "20", "30"],
                    default_value="10",
                    tag="settings_fps",
                    width=150,
                    callback=self._on_setting_change
                )

            dpg.add_spacer(height=5)

            # Threshold
            with dpg.group(horizontal=True):
                dpg.add_text("Threshold:", color=COLORS['text_dim'], indent=10)
                dpg.add_slider_float(
                    default_value=0.75,
                    min_value=0.5,
                    max_value=0.95,
                    tag="settings_threshold",
                    width=150,
                    format="%.2f",
                    callback=self._on_setting_change
                )

            dpg.add_spacer(height=5)

            # Cooldown
            with dpg.group(horizontal=True):
                dpg.add_text("Cooldown:", color=COLORS['text_dim'], indent=10)
                dpg.add_combo(
                    items=["3 sec", "5 sec", "10 sec"],
                    default_value="5 sec",
                    tag="settings_cooldown",
                    width=150,
                    callback=self._on_setting_change
                )

            dpg.add_spacer(height=15)

            # Hotkeys section
            dpg.add_text("HOTKEYS", color=COLORS['text_dim'])
            dpg.add_spacer(height=5)

            hotkeys = [
                ("Manual Death:", "hotkey_death", "Ctrl+Shift+D"),
                ("Toggle Boss:", "hotkey_boss", "Ctrl+Shift+B"),
                ("Toggle Mode:", "hotkey_mode", "Ctrl+Shift+O"),
                ("Pause Detect:", "hotkey_detect", "Ctrl+Shift+P"),
            ]

            for label, tag, default in hotkeys:
                with dpg.group(horizontal=True):
                    dpg.add_text(label, color=COLORS['text_dim'], indent=10)
                    dpg.add_button(
                        label=default,
                        tag=tag,
                        width=150,
                        callback=lambda s, a, u: self._start_hotkey_recording(u),
                        user_data=tag
                    )

            dpg.add_spacer(height=15)

            # Window section
            dpg.add_text("WINDOW", color=COLORS['text_dim'])
            dpg.add_spacer(height=5)

            dpg.add_checkbox(label="Start minimized", tag="settings_start_minimized", indent=10)
            dpg.add_checkbox(label="Always on top (compact)", tag="settings_always_on_top", default_value=True, indent=10)

            with dpg.group(horizontal=True):
                dpg.add_text("Opacity:", color=COLORS['text_dim'], indent=10)
                dpg.add_slider_float(
                    default_value=0.9,
                    min_value=0.5,
                    max_value=1.0,
                    tag="settings_opacity",
                    width=150,
                    format="%.1f",
                    callback=self._on_setting_change
                )

    def update(self, profile: str, connected: bool):
        """Update profile display."""
        if dpg.does_item_exist("settings_profile_name"):
            dpg.set_value("settings_profile_name", profile or "Not connected")

        if dpg.does_item_exist("settings_profile_status"):
            if connected:
                dpg.set_value("settings_profile_status", "Connected")
                dpg.configure_item("settings_profile_status", color=COLORS['success'])
            else:
                dpg.set_value("settings_profile_status", "Disconnected")
                dpg.configure_item("settings_profile_status", color=COLORS['accent'])

    def load_from_config(self):
        """Load settings from config."""
        if dpg.does_item_exist("settings_monitor"):
            monitor = self.config.get('detection.monitor', 0)
            dpg.set_value("settings_monitor", f"Display {monitor + 1}")

        if dpg.does_item_exist("settings_fps"):
            fps = self.config.get('detection.fps', 10)
            dpg.set_value("settings_fps", str(fps))

        if dpg.does_item_exist("settings_threshold"):
            threshold = self.config.get('detection.death_threshold', 0.75)
            dpg.set_value("settings_threshold", threshold)

        if dpg.does_item_exist("settings_cooldown"):
            cooldown = self.config.get('detection.death_cooldown', 5.0)
            dpg.set_value("settings_cooldown", f"{int(cooldown)} sec")

    def _on_change_profile(self):
        self.on_change_profile()

    def _on_setting_change(self, sender, app_data):
        """Handle setting change - collect and save."""
        settings = self._collect_settings()
        self.on_save_settings(settings)

    def _collect_settings(self) -> Dict:
        """Collect all settings values."""
        settings = {}

        if dpg.does_item_exist("settings_monitor"):
            val = dpg.get_value("settings_monitor")
            settings['detection.monitor'] = int(val.split()[-1]) - 1

        if dpg.does_item_exist("settings_fps"):
            settings['detection.fps'] = int(dpg.get_value("settings_fps"))

        if dpg.does_item_exist("settings_threshold"):
            settings['detection.death_threshold'] = dpg.get_value("settings_threshold")

        if dpg.does_item_exist("settings_cooldown"):
            val = dpg.get_value("settings_cooldown")
            settings['detection.death_cooldown'] = float(val.split()[0])

        if dpg.does_item_exist("settings_start_minimized"):
            settings['window.start_minimized'] = dpg.get_value("settings_start_minimized")

        if dpg.does_item_exist("settings_always_on_top"):
            settings['window.always_on_top'] = dpg.get_value("settings_always_on_top")

        if dpg.does_item_exist("settings_opacity"):
            settings['overlay.opacity'] = dpg.get_value("settings_opacity")

        return settings

    def _start_hotkey_recording(self, tag: str):
        """Start recording a hotkey."""
        self._recording_hotkey = tag
        if dpg.does_item_exist(tag):
            dpg.set_item_label(tag, "Press keys...")
        # TODO: Integrate with pynput for actual recording
