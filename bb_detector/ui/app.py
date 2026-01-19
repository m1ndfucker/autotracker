# bb_detector/ui/app.py
"""Main application window with sidebar navigation."""
import dearpygui.dearpygui as dpg
from typing import Optional, Callable
from pathlib import Path
import sys

from .theme import (
    create_theme,
    create_sidebar_theme,
    create_sidebar_item_theme,
    COLORS,
)
from .sections.play import PlaySection
from .sections.setup import SetupSection
from .sections.history import HistorySection
from .compact import CompactWindow
from .dialogs.profile import ProfileDialog
from ..state import StateManager
from ..config import Config


class App:
    """Main application window manager with sidebar navigation."""

    FULL_WIDTH = 600
    FULL_HEIGHT = 500
    SIDEBAR_WIDTH = 150

    def __init__(
        self,
        config: Config,
        state: StateManager,
        # Callbacks for actions
        on_manual_death: Callable,
        on_timer_start: Callable,
        on_timer_stop: Callable,
        on_timer_reset: Callable,
        on_boss_start: Callable,
        on_boss_pause: Callable,
        on_boss_resume: Callable,
        on_boss_victory: Callable,
        on_boss_cancel: Callable,
        on_toggle_detection: Callable,
        on_profile_select: Callable,
        on_capture: Callable,
        on_capture_region: Callable,
        on_test_detection: Callable,
        on_save_region: Callable,
        on_quit: Callable,
        on_f9_pressed: Callable = None,
        # Milestone callbacks
        on_add_milestone: Callable = None,
        on_delete_milestone: Callable = None,
        # Stats callbacks
        on_add_stats: Callable = None,
        on_delete_stats: Callable = None,
    ):
        self.config = config
        self.state = state

        # Store callbacks
        self._on_manual_death = on_manual_death
        self._on_timer_start = on_timer_start
        self._on_timer_stop = on_timer_stop
        self._on_timer_reset = on_timer_reset
        self._on_boss_start = on_boss_start
        self._on_boss_pause = on_boss_pause
        self._on_boss_resume = on_boss_resume
        self._on_boss_victory = on_boss_victory
        self._on_boss_cancel = on_boss_cancel
        self._on_toggle_detection = on_toggle_detection
        self._on_profile_select = on_profile_select
        self._on_capture = on_capture
        self._on_capture_region = on_capture_region
        self._on_test_detection = on_test_detection
        self._on_save_region = on_save_region
        self._on_quit = on_quit
        self._on_add_milestone = on_add_milestone or (lambda n, i: None)
        self._on_delete_milestone = on_delete_milestone or (lambda i: None)
        self._on_add_stats = on_add_stats or (lambda s: None)
        self._on_delete_stats = on_delete_stats or (lambda i: None)

        # UI components (sections instead of tabs)
        self.play_section: Optional[PlaySection] = None
        self.setup_section: Optional[SetupSection] = None
        self.history_section: Optional[HistorySection] = None
        self.compact_window: Optional[CompactWindow] = None

        # Current active section
        self._current_section = "play"

        # Sidebar themes (active/inactive)
        self._sidebar_theme: Optional[int] = None
        self._sidebar_item_active_theme: Optional[int] = None
        self._sidebar_item_inactive_theme: Optional[int] = None

        self._is_compact = False
        self._running = False

    def _load_fonts(self):
        """Load fonts with Cyrillic support."""
        # Find a font that supports Cyrillic
        font_paths = []

        # macOS system fonts
        if sys.platform == 'darwin':
            font_paths = [
                '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
                '/System/Library/Fonts/Helvetica.ttc',
                '/Library/Fonts/Arial Unicode.ttf',
                '/System/Library/Fonts/SFNS.ttf',
            ]
        # Windows system fonts
        elif sys.platform == 'win32':
            font_paths = [
                'C:/Windows/Fonts/arial.ttf',
                'C:/Windows/Fonts/segoeui.ttf',
                'C:/Windows/Fonts/tahoma.ttf',
            ]

        # Find first existing font
        font_path = None
        for fp in font_paths:
            if Path(fp).exists():
                font_path = fp
                break

        if not font_path:
            print("[UI] No Cyrillic font found, using default", flush=True)
            return

        try:
            with dpg.font_registry():
                # Load font with extended glyph ranges
                with dpg.font(font_path, 16) as font:
                    # Add Cyrillic range (0x0400-0x04FF)
                    dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
                    # Add default Latin range
                    dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)

                dpg.bind_font(font)
                print(f"[UI] Loaded font: {font_path}", flush=True)
        except Exception as e:
            print(f"[UI] Font loading failed: {e}", flush=True)

    def init(self):
        """Initialize DearPyGui and create windows."""
        dpg.create_context()

        # Load font with Cyrillic support
        self._load_fonts()

        # Create viewport
        dpg.create_viewport(
            title="BB Death Detector",
            width=self.FULL_WIDTH,
            height=self.FULL_HEIGHT,
            resizable=False,
        )

        # Apply theme
        theme = create_theme()
        dpg.bind_theme(theme)

        # Create sidebar themes
        self._sidebar_theme = create_sidebar_theme()
        self._sidebar_item_active_theme = create_sidebar_item_theme(active=True)
        self._sidebar_item_inactive_theme = create_sidebar_item_theme(active=False)

        # Create main window
        self._create_main_window()

        # Create compact window (hidden)
        self.compact_window = CompactWindow(on_expand=self._switch_to_full)
        self.compact_window.create()

        # Subscribe to state changes
        self.state.subscribe(self._on_state_change)

        # Setup
        dpg.setup_dearpygui()
        dpg.show_viewport()

        self._running = True

    def _create_main_window(self):
        """Create the main window with sidebar layout."""
        with dpg.window(tag="main_window", label="", no_title_bar=True, no_resize=True, no_move=True):
            # Configure to fill viewport
            dpg.set_primary_window("main_window", True)

            # Header
            with dpg.group(horizontal=True):
                dpg.add_text("BB Death Detector", color=COLORS['text'])
                dpg.add_spacer(width=300)
                dpg.add_button(label="[_]", width=30, callback=self._switch_to_compact)
                dpg.add_button(label="[X]", width=30, callback=self._on_quit)

            dpg.add_separator()
            dpg.add_spacer(height=5)

            # Main content area: Sidebar + Content
            with dpg.group(horizontal=True):
                # === Sidebar (150px) ===
                with dpg.child_window(
                    tag="sidebar",
                    width=self.SIDEBAR_WIDTH,
                    height=440,
                    border=False,
                ) as sidebar:
                    dpg.bind_item_theme(sidebar, self._sidebar_theme)

                    dpg.add_spacer(height=10)

                    # Navigation buttons
                    btn_play = dpg.add_button(
                        label="Play",
                        tag="nav_play",
                        width=-1,
                        height=36,
                        callback=lambda: self._switch_section("play"),
                    )
                    dpg.bind_item_theme(btn_play, self._sidebar_item_active_theme)

                    dpg.add_spacer(height=4)

                    btn_setup = dpg.add_button(
                        label="Setup",
                        tag="nav_setup",
                        width=-1,
                        height=36,
                        callback=lambda: self._switch_section("setup"),
                    )
                    dpg.bind_item_theme(btn_setup, self._sidebar_item_inactive_theme)

                    dpg.add_spacer(height=4)

                    btn_history = dpg.add_button(
                        label="History",
                        tag="nav_history",
                        width=-1,
                        height=36,
                        callback=lambda: self._switch_section("history"),
                    )
                    dpg.bind_item_theme(btn_history, self._sidebar_item_inactive_theme)

                    # Spacer to push status to bottom
                    dpg.add_spacer(height=240)

                    # Separator before status
                    dpg.add_separator()
                    dpg.add_spacer(height=8)

                    # Connection status
                    with dpg.group(horizontal=True):
                        dpg.add_text("", tag="sidebar_status_indicator", color=COLORS['accent'])
                        dpg.add_text("Offline", tag="sidebar_status_text", color=COLORS['text_dim'])

                    dpg.add_spacer(height=4)

                    # Profile name
                    dpg.add_text("", tag="sidebar_profile_name", color=COLORS['text_secondary'])

                    dpg.add_spacer(height=8)

                    # Change profile button
                    dpg.add_button(
                        label="Change",
                        tag="sidebar_change_profile_btn",
                        width=80,
                        height=24,
                        callback=self._show_profile_dialog,
                    )

                # === Content Area (450px) ===
                with dpg.child_window(
                    tag="content_area",
                    width=-1,
                    height=440,
                    border=False,
                ):
                    # Play section
                    self.play_section = PlaySection(
                        on_manual_death=self._on_manual_death,
                        on_timer_start=self._on_timer_start,
                        on_timer_stop=self._on_timer_stop,
                        on_timer_reset=self._on_timer_reset,
                        on_boss_start=self._on_boss_start,
                        on_boss_pause=self._on_boss_pause,
                        on_boss_resume=self._on_boss_resume,
                        on_boss_victory=self._on_boss_victory,
                        on_boss_cancel=self._on_boss_cancel,
                        on_toggle_detection=self._on_toggle_detection,
                    )
                    self.play_section.create("content_area")

                    # Setup section (hidden by default)
                    self.setup_section = SetupSection(
                        config=self.config,
                        on_capture=self._on_capture,
                        on_capture_region=self._on_capture_region,
                        on_test_detection=self._on_test_detection,
                        on_save_region=self._on_save_region,
                        on_save_settings=self._save_settings,
                    )
                    self.setup_section.create("content_area")
                    self.setup_section.hide()

                    # History section (hidden by default)
                    self.history_section = HistorySection(
                        on_add_milestone=self._on_add_milestone,
                        on_delete_milestone=self._on_delete_milestone,
                        on_add_stats=self._on_add_stats,
                        on_delete_stats=self._on_delete_stats,
                    )
                    self.history_section.create("content_area")
                    self.history_section.hide()

    def _switch_section(self, section: str):
        """Switch to a different section, updating visibility and nav button themes."""
        if section == self._current_section:
            return

        self._current_section = section

        # Update section visibility
        if self.play_section:
            if section == "play":
                self.play_section.show()
            else:
                self.play_section.hide()

        if self.setup_section:
            if section == "setup":
                self.setup_section.show()
            else:
                self.setup_section.hide()

        if self.history_section:
            if section == "history":
                self.history_section.show()
            else:
                self.history_section.hide()

        # Update nav button themes
        nav_buttons = ["nav_play", "nav_setup", "nav_history"]
        section_map = {"play": "nav_play", "setup": "nav_setup", "history": "nav_history"}

        for btn_tag in nav_buttons:
            if dpg.does_item_exist(btn_tag):
                if btn_tag == section_map[section]:
                    dpg.bind_item_theme(btn_tag, self._sidebar_item_active_theme)
                else:
                    dpg.bind_item_theme(btn_tag, self._sidebar_item_inactive_theme)

    def show_profile_dialog(self):
        """Show profile selection dialog."""
        dialog = ProfileDialog(
            on_select=self._on_profile_selected,
            on_cancel=self._on_profile_cancel
        )
        dialog.show()

    def _show_profile_dialog(self):
        """Internal: show profile dialog from sidebar."""
        self.show_profile_dialog()

    def _on_profile_selected(self, name: str, password: str, is_new: bool):
        """Handle profile selection."""
        self._on_profile_select(name, password, is_new)

    def _on_profile_cancel(self):
        """Handle profile dialog cancel."""
        # If no profile configured, quit
        if not self.config.get('profile.name'):
            self._on_quit()

    def _save_settings(self, settings: dict):
        """Save settings to config."""
        for key, value in settings.items():
            self.config.set(key, value)
        self.config.save()

    def _switch_to_compact(self):
        """Switch to compact mode."""
        if dpg.does_item_exist("main_window"):
            dpg.configure_item("main_window", show=False)
        self.compact_window.show()
        self._is_compact = True

    def _switch_to_full(self):
        """Switch to full mode."""
        self.compact_window.hide()
        if dpg.does_item_exist("main_window"):
            dpg.configure_item("main_window", show=True)
        self._is_compact = False

    def toggle_mode(self):
        """Toggle between compact and full mode."""
        if self._is_compact:
            self._switch_to_full()
        else:
            self._switch_to_compact()

    def on_f9_pressed(self):
        """Handle F9 hotkey press, pass to setup section if active."""
        if self.setup_section:
            self.setup_section.on_f9_pressed()

    def _on_state_change(self, key: str, value):
        """Handle state changes."""
        # Update UI based on state
        self._update_ui()

    def _update_ui(self):
        """Update all UI elements from state."""
        # Update play section
        if self.play_section:
            self.play_section.update(
                deaths=self.state.deaths,
                elapsed=self.state.elapsed,
                is_running=self.state.is_running,
                boss_mode=self.state.boss_mode,
                boss_deaths=self.state.boss_deaths,
                boss_paused=self.state.boss_paused,
                detection_enabled=self.state.detection_enabled,
            )

        # Update history section
        if self.history_section:
            self.history_section.update(
                deaths=self.state.deaths,
                elapsed=self.state.elapsed,
                milestones=self.state.get('milestones', []),
                death_timestamps=self.state.get('death_timestamps', []),
                boss_fights=self.state.get('boss_fights', []),
                character_stats=self.state.get('character_stats', []),
            )

        # Update compact window
        if self.compact_window:
            self.compact_window.update(
                deaths=self.state.deaths,
                elapsed=self.state.elapsed,
                boss_mode=self.state.boss_mode,
                boss_deaths=self.state.boss_deaths,
                connected=self.state.connected,
                profile=self.state.profile_display_name or self.state.profile or "",
            )

        # Update sidebar status
        if dpg.does_item_exist("sidebar_status_indicator"):
            if self.state.connected:
                dpg.set_value("sidebar_status_indicator", "")
                dpg.configure_item("sidebar_status_indicator", color=COLORS['success'])
            else:
                dpg.set_value("sidebar_status_indicator", "")
                dpg.configure_item("sidebar_status_indicator", color=COLORS['accent'])

        if dpg.does_item_exist("sidebar_status_text"):
            if self.state.connected:
                dpg.set_value("sidebar_status_text", "Online")
                dpg.configure_item("sidebar_status_text", color=COLORS['success'])
            else:
                dpg.set_value("sidebar_status_text", "Offline")
                dpg.configure_item("sidebar_status_text", color=COLORS['text_dim'])

        if dpg.does_item_exist("sidebar_profile_name"):
            profile = self.state.profile_display_name or self.state.profile or ""
            dpg.set_value("sidebar_profile_name", profile)

    def render(self):
        """Render one frame."""
        if self._running:
            # Process pending updates from setup section (thread-safe)
            if self.setup_section:
                self.setup_section.update()
            dpg.render_dearpygui_frame()

    def is_running(self) -> bool:
        """Check if app is still running."""
        return self._running and dpg.is_dearpygui_running()

    def destroy(self):
        """Cleanup and destroy DearPyGui context."""
        self._running = False
        dpg.destroy_context()
