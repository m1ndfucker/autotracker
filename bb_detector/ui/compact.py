# bb_detector/ui/compact.py
"""Compact mode window - minimal overlay during gameplay."""
import dearpygui.dearpygui as dpg
from typing import Callable, Optional
from .theme import COLORS, create_accent_button_theme, create_boss_button_theme, create_success_button_theme
from ..dialogs.milestone import MilestoneDialog
from ..dialogs.stats import StatsDialog


class CompactWindow:
    """Compact overlay window showing essential info during gameplay."""

    WIDTH = 280
    HEIGHT = 160

    def __init__(
        self,
        on_expand: Callable[[], None],
        on_boss_start: Optional[Callable[[], None]] = None,
        on_boss_pause: Optional[Callable[[], None]] = None,
        on_boss_resume: Optional[Callable[[], None]] = None,
        on_boss_victory: Optional[Callable[[], None]] = None,
        on_boss_cancel: Optional[Callable[[], None]] = None,
        on_add_milestone: Optional[Callable[[str, str], None]] = None,
        on_add_stats: Optional[Callable[[dict], None]] = None,
    ):
        self.on_expand = on_expand
        self.on_boss_start = on_boss_start or (lambda: None)
        self.on_boss_pause = on_boss_pause or (lambda: None)
        self.on_boss_resume = on_boss_resume or (lambda: None)
        self.on_boss_victory = on_boss_victory or (lambda: None)
        self.on_boss_cancel = on_boss_cancel or (lambda: None)
        self.on_add_milestone = on_add_milestone or (lambda n, i: None)
        self.on_add_stats = on_add_stats or (lambda s: None)

        self._visible = False
        self._position = [50, 50]
        self._boss_mode = False
        self._boss_paused = False

        # Themes
        self._accent_theme = None
        self._boss_theme = None
        self._success_theme = None

    def create(self):
        """Create the compact window (hidden initially)."""
        # Create button themes
        self._accent_theme = create_accent_button_theme()
        self._boss_theme = create_boss_button_theme()
        self._success_theme = create_success_button_theme()

        with dpg.window(
            tag="compact_window",
            label="BB Detector",
            width=self.WIDTH,
            height=self.HEIGHT,
            pos=self._position,
            no_title_bar=True,
            no_resize=True,
            no_scrollbar=True,
            no_collapse=True,
            show=False,
        ):
            # === Header row: Deaths, Timer, Expand button ===
            with dpg.group(horizontal=True):
                # Deaths counter (skull icon + count)
                dpg.add_text("☠", color=COLORS['red'])
                dpg.add_text("0", tag="compact_deaths", color=COLORS['red'])

                dpg.add_spacer(width=40)

                # Timer
                dpg.add_text("00:00:00", tag="compact_timer", color=COLORS['text_primary'])

                dpg.add_spacer(width=40)

                # Expand button
                expand_btn = dpg.add_button(
                    label="[+]",
                    tag="compact_expand_btn",
                    callback=self._on_expand_click,
                    width=30
                )

            dpg.add_separator()

            # === Boss section ===
            with dpg.group(tag="compact_boss_section"):
                # Boss mode label
                dpg.add_text("Boss Mode: OFF", tag="compact_boss_label", color=COLORS['text_tertiary'])

                dpg.add_spacer(height=2)

                # Boss controls - inactive state (Start Boss button)
                with dpg.group(horizontal=True, tag="compact_boss_inactive"):
                    start_btn = dpg.add_button(
                        label="Start Boss",
                        tag="compact_start_boss_btn",
                        callback=self._on_boss_start,
                        width=-1
                    )
                    dpg.bind_item_theme(start_btn, self._boss_theme)

                # Boss controls - active state (Victory, Pause/Resume, Cancel)
                with dpg.group(horizontal=True, tag="compact_boss_active", show=False):
                    victory_btn = dpg.add_button(
                        label="Victory",
                        tag="compact_victory_btn",
                        callback=self._on_boss_victory,
                        width=80
                    )
                    dpg.bind_item_theme(victory_btn, self._success_theme)

                    pause_btn = dpg.add_button(
                        label="Pause",
                        tag="compact_pause_btn",
                        callback=self._on_boss_pause,
                        width=80
                    )

                    cancel_btn = dpg.add_button(
                        label="Cancel",
                        tag="compact_cancel_btn",
                        callback=self._on_boss_cancel,
                        width=70
                    )
                    dpg.bind_item_theme(cancel_btn, self._accent_theme)

            dpg.add_separator()

            # === Quick add buttons ===
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="+ Milestone",
                    tag="compact_add_milestone_btn",
                    callback=self._on_add_milestone_click,
                    width=125
                )
                dpg.add_button(
                    label="+ Stats",
                    tag="compact_add_stats_btn",
                    callback=self._on_add_stats_click,
                    width=125
                )

            dpg.add_spacer(height=2)

            # === Status bar ===
            with dpg.group(horizontal=True):
                dpg.add_text("●", tag="compact_status_dot", color=COLORS['text_tertiary'])
                dpg.add_text("Offline", tag="compact_status_text", color=COLORS['text_tertiary'])

                dpg.add_spacer(width=100)

                dpg.add_text("", tag="compact_profile", color=COLORS['text_secondary'])

    def show(self):
        """Show compact window."""
        if dpg.does_item_exist("compact_window"):
            dpg.configure_item("compact_window", show=True)
            self._visible = True

    def hide(self):
        """Hide compact window."""
        if dpg.does_item_exist("compact_window"):
            # Save position before hiding
            self._position = dpg.get_item_pos("compact_window")
            dpg.configure_item("compact_window", show=False)
            self._visible = False

    def is_visible(self) -> bool:
        return self._visible

    def update(self, deaths: int, elapsed: int, boss_mode: bool,
               boss_deaths: int, connected: bool, profile: str,
               boss_paused: bool = False):
        """Update compact display."""
        self._boss_mode = boss_mode
        self._boss_paused = boss_paused

        # Deaths counter
        if dpg.does_item_exist("compact_deaths"):
            dpg.set_value("compact_deaths", str(deaths))

        # Timer
        if dpg.does_item_exist("compact_timer"):
            hours = elapsed // 3600000
            minutes = (elapsed % 3600000) // 60000
            seconds = (elapsed % 60000) // 1000
            dpg.set_value("compact_timer", f"{hours:02d}:{minutes:02d}:{seconds:02d}")

        # Boss mode UI
        self._update_boss_ui(boss_mode, boss_deaths, boss_paused)

        # Connection status
        if dpg.does_item_exist("compact_status_dot"):
            if connected:
                dpg.set_value("compact_status_dot", "●")
                dpg.configure_item("compact_status_dot", color=COLORS['green'])
            else:
                dpg.set_value("compact_status_dot", "●")
                dpg.configure_item("compact_status_dot", color=COLORS['text_tertiary'])

        if dpg.does_item_exist("compact_status_text"):
            if connected:
                dpg.set_value("compact_status_text", "Online")
                dpg.configure_item("compact_status_text", color=COLORS['green'])
            else:
                dpg.set_value("compact_status_text", "Offline")
                dpg.configure_item("compact_status_text", color=COLORS['text_tertiary'])

        # Profile name
        if dpg.does_item_exist("compact_profile"):
            dpg.set_value("compact_profile", profile if profile else "")

    def _update_boss_ui(self, boss_mode: bool, boss_deaths: int, boss_paused: bool):
        """Update boss section UI based on state."""
        # Boss label
        if dpg.does_item_exist("compact_boss_label"):
            if boss_mode:
                status = " (PAUSED)" if boss_paused else ""
                dpg.set_value("compact_boss_label", f"BOSS ACTIVE: {boss_deaths} deaths{status}")
                dpg.configure_item("compact_boss_label", color=COLORS['purple'])
            else:
                dpg.set_value("compact_boss_label", "Boss Mode: OFF")
                dpg.configure_item("compact_boss_label", color=COLORS['text_tertiary'])

        # Toggle visibility of control groups
        if dpg.does_item_exist("compact_boss_inactive"):
            dpg.configure_item("compact_boss_inactive", show=not boss_mode)

        if dpg.does_item_exist("compact_boss_active"):
            dpg.configure_item("compact_boss_active", show=boss_mode)

        # Update pause/resume button label
        if dpg.does_item_exist("compact_pause_btn"):
            if boss_paused:
                dpg.configure_item("compact_pause_btn", label="Resume")
            else:
                dpg.configure_item("compact_pause_btn", label="Pause")

    def set_position(self, x: int, y: int):
        """Set window position."""
        self._position = [x, y]
        if dpg.does_item_exist("compact_window"):
            dpg.set_item_pos("compact_window", self._position)

    def get_position(self) -> list:
        """Get current window position."""
        if dpg.does_item_exist("compact_window"):
            return dpg.get_item_pos("compact_window")
        return self._position

    # === Callbacks ===

    def _on_expand_click(self):
        """Handle expand button click."""
        self.on_expand()

    def _on_boss_start(self):
        """Handle start boss button click."""
        self.on_boss_start()

    def _on_boss_pause(self):
        """Handle pause/resume button click."""
        if self._boss_paused:
            self.on_boss_resume()
        else:
            self.on_boss_pause()

    def _on_boss_victory(self):
        """Handle victory button click."""
        self.on_boss_victory()

    def _on_boss_cancel(self):
        """Handle cancel button click."""
        self.on_boss_cancel()

    def _on_add_milestone_click(self):
        """Handle add milestone button click."""
        dialog = MilestoneDialog(
            on_add=self.on_add_milestone,
            on_cancel=lambda: None
        )
        dialog.show()

    def _on_add_stats_click(self):
        """Handle add stats button click."""
        dialog = StatsDialog(
            on_add=self.on_add_stats,
            on_cancel=lambda: None
        )
        dialog.show()
