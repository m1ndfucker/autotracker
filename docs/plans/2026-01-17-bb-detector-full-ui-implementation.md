# BB Death Detector Full UI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace minimal overlay with full-featured desktop application: main window with tabs (Play/Settings/Calibration), compact mode, profile selection wizard.

**Architecture:** Single dearpygui context manages both full and compact modes. State manager centralizes app state, UI subscribes to changes. WebSocket client updates state, UI renders from state.

**Tech Stack:** Python 3.12, dearpygui 1.11+, websockets, pynput, mss/bettercam, opencv-python

---

## Phase 1: Foundation

### Task 1: Create State Manager

**Files:**
- Create: `bb_detector/state.py`
- Test: `tests/test_state.py`

**Step 1: Write the failing test**

```python
# tests/test_state.py
import pytest

def test_state_manager_init():
    """State manager initializes with defaults"""
    from bb_detector.state import StateManager

    state = StateManager()

    assert state.deaths == 0
    assert state.elapsed == 0
    assert state.is_running == False
    assert state.boss_mode == False
    assert state.connected == False

def test_state_manager_subscribe():
    """State manager notifies subscribers on change"""
    from bb_detector.state import StateManager

    state = StateManager()
    notifications = []

    state.subscribe(lambda key, val: notifications.append((key, val)))
    state.set('deaths', 42)

    assert state.deaths == 42
    assert ('deaths', 42) in notifications

def test_state_manager_update_from_server():
    """State manager updates from server state dict"""
    from bb_detector.state import StateManager

    state = StateManager()
    state.update_from_server({
        'deaths': 10,
        'elapsed': 5000,
        'isRunning': True,
        'bossFightMode': True,
        'bossDeaths': 2,
        'canEdit': True
    })

    assert state.deaths == 10
    assert state.elapsed == 5000
    assert state.is_running == True
    assert state.boss_mode == True
    assert state.boss_deaths == 2
    assert state.can_edit == True
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/warezzko/Desktop/netfl/bb-detector && source .venv/bin/activate && python -m pytest tests/test_state.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'bb_detector.state'"

**Step 3: Write implementation**

```python
# bb_detector/state.py
from typing import Any, Callable, Dict, List

class StateManager:
    """Centralized state management with subscriber notifications."""

    def __init__(self):
        self._state: Dict[str, Any] = {
            'deaths': 0,
            'elapsed': 0,
            'is_running': False,
            'boss_mode': False,
            'boss_deaths': 0,
            'boss_paused': False,
            'connected': False,
            'can_edit': False,
            'detection_enabled': True,
            'profile': None,
            'profile_display_name': None,
        }
        self._subscribers: List[Callable[[str, Any], None]] = []

    def __getattr__(self, name: str) -> Any:
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        if name in self._state:
            return self._state[name]
        raise AttributeError(f"State has no attribute '{name}'")

    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        if key in self._state:
            old_value = self._state[key]
            if old_value != value:
                self._state[key] = value
                self._notify(key, value)

    def subscribe(self, callback: Callable[[str, Any], None]) -> None:
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[str, Any], None]) -> None:
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def _notify(self, key: str, value: Any) -> None:
        for callback in self._subscribers:
            try:
                callback(key, value)
            except Exception:
                pass

    def update_from_server(self, data: Dict[str, Any]) -> None:
        """Update state from server bb-state message."""
        mapping = {
            'deaths': 'deaths',
            'elapsed': 'elapsed',
            'isRunning': 'is_running',
            'bossFightMode': 'boss_mode',
            'bossDeaths': 'boss_deaths',
            'bossPaused': 'boss_paused',
            'canEdit': 'can_edit',
            'profileName': 'profile',
            'displayName': 'profile_display_name',
        }

        for server_key, local_key in mapping.items():
            if server_key in data:
                self.set(local_key, data[server_key])

    def to_dict(self) -> Dict[str, Any]:
        return self._state.copy()
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/warezzko/Desktop/netfl/bb-detector && source .venv/bin/activate && python -m pytest tests/test_state.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add bb_detector/state.py tests/test_state.py
git commit -m "feat: add centralized state manager"
```

---

### Task 2: Create UI Theme Module

**Files:**
- Create: `bb_detector/ui/__init__.py`
- Create: `bb_detector/ui/theme.py`

**Step 1: Create ui package**

```python
# bb_detector/ui/__init__.py
"""UI components for BB Death Detector."""
```

**Step 2: Create theme module**

```python
# bb_detector/ui/theme.py
"""DearPyGui theme configuration."""
import dearpygui.dearpygui as dpg

# Color palette (dark theme)
COLORS = {
    'bg': (15, 15, 17, 255),
    'bg_secondary': (26, 26, 30, 255),
    'bg_hover': (35, 35, 40, 255),
    'text': (240, 236, 228, 255),
    'text_dim': (140, 140, 140, 255),
    'accent': (196, 48, 48, 255),       # Red for deaths
    'accent_hover': (220, 70, 70, 255),
    'success': (72, 187, 120, 255),     # Green for connected
    'warning': (236, 201, 75, 255),     # Yellow
    'boss': (147, 112, 219, 255),       # Purple for boss mode
    'border': (60, 60, 65, 255),
}

def create_theme() -> int:
    """Create and return the main application theme."""
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvAll):
            # Window
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, COLORS['bg'])
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, COLORS['bg_secondary'])
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, COLORS['bg_secondary'])

            # Text
            dpg.add_theme_color(dpg.mvThemeCol_Text, COLORS['text'])
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, COLORS['text_dim'])

            # Borders
            dpg.add_theme_color(dpg.mvThemeCol_Border, COLORS['border'])
            dpg.add_theme_color(dpg.mvThemeCol_BorderShadow, (0, 0, 0, 0))

            # Frame (inputs, buttons)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, COLORS['bg_secondary'])
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, COLORS['bg_hover'])
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, COLORS['bg_hover'])

            # Buttons
            dpg.add_theme_color(dpg.mvThemeCol_Button, COLORS['bg_secondary'])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, COLORS['bg_hover'])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, COLORS['accent'])

            # Headers/Tabs
            dpg.add_theme_color(dpg.mvThemeCol_Header, COLORS['bg_secondary'])
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, COLORS['bg_hover'])
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, COLORS['accent'])

            dpg.add_theme_color(dpg.mvThemeCol_Tab, COLORS['bg_secondary'])
            dpg.add_theme_color(dpg.mvThemeCol_TabHovered, COLORS['bg_hover'])
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, COLORS['bg'])
            dpg.add_theme_color(dpg.mvThemeCol_TabUnfocused, COLORS['bg_secondary'])
            dpg.add_theme_color(dpg.mvThemeCol_TabUnfocusedActive, COLORS['bg'])

            # Slider
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, COLORS['accent'])
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, COLORS['accent_hover'])

            # Checkbox
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, COLORS['accent'])

            # Separator
            dpg.add_theme_color(dpg.mvThemeCol_Separator, COLORS['border'])

            # Rounding
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 4)

            # Padding
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 6)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 12, 12)

    return theme

def create_accent_button_theme() -> int:
    """Create theme for accent (red) buttons."""
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, COLORS['accent'])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, COLORS['accent_hover'])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (150, 40, 40, 255))
    return theme

def create_success_button_theme() -> int:
    """Create theme for success (green) buttons."""
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, COLORS['success'])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (90, 210, 140, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (60, 160, 100, 255))
    return theme

def create_boss_button_theme() -> int:
    """Create theme for boss (purple) buttons."""
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, COLORS['boss'])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (170, 140, 240, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (120, 90, 190, 255))
    return theme
```

**Step 3: Commit**

```bash
mkdir -p bb_detector/ui
git add bb_detector/ui/__init__.py bb_detector/ui/theme.py
git commit -m "feat: add UI theme module with dark color palette"
```

---

### Task 3: Create Profile Dialog

**Files:**
- Create: `bb_detector/ui/profile_dialog.py`

**Step 1: Write implementation**

```python
# bb_detector/ui/profile_dialog.py
"""Profile selection dialog for first run and profile changes."""
import dearpygui.dearpygui as dpg
from typing import Callable, List, Dict, Optional
import requests

class ProfileDialog:
    """Modal dialog for selecting or creating a profile."""

    API_URL = "https://watch.home.kg/api/bb-profiles"

    def __init__(self, on_select: Callable[[str, str, bool], None], on_cancel: Callable[[], None]):
        """
        Args:
            on_select: Callback(profile_name, password, is_new_profile)
            on_cancel: Callback when cancelled
        """
        self.on_select = on_select
        self.on_cancel = on_cancel
        self.profiles: List[Dict] = []
        self.selected_profile: Optional[str] = None
        self._window_id = None

    def show(self):
        """Show the profile selection dialog."""
        self._fetch_profiles()
        self._create_window()

    def _fetch_profiles(self):
        """Fetch public profiles from server."""
        try:
            response = requests.get(self.API_URL, timeout=5)
            if response.ok:
                data = response.json()
                self.profiles = data.get('profiles', [])
        except Exception:
            self.profiles = []

    def _create_window(self):
        """Create the dialog window."""
        # Center position
        viewport_width = dpg.get_viewport_width()
        viewport_height = dpg.get_viewport_height()
        window_width = 400
        window_height = 450

        with dpg.window(
            label="BB Death Detector",
            tag="profile_dialog",
            width=window_width,
            height=window_height,
            pos=[(viewport_width - window_width) // 2, (viewport_height - window_height) // 2],
            no_resize=True,
            no_move=False,
            no_collapse=True,
            modal=True,
            on_close=self._on_cancel_click
        ) as self._window_id:

            dpg.add_spacer(height=10)
            dpg.add_text("Select or create a profile to start", color=(180, 180, 180))
            dpg.add_spacer(height=15)

            # Public profiles section
            dpg.add_text("PUBLIC PROFILES")

            with dpg.child_window(height=150, border=True):
                if self.profiles:
                    for profile in self.profiles[:10]:  # Limit to 10
                        name = profile.get('name', '')
                        display = profile.get('displayName', name)
                        deaths = profile.get('deaths', 0)

                        with dpg.group(horizontal=True):
                            dpg.add_radio_button(
                                items=[f"{display} ({deaths} deaths)"],
                                tag=f"profile_radio_{name}",
                                callback=lambda s, a, u: self._on_profile_select(u),
                                user_data=name
                            )
                else:
                    dpg.add_text("No public profiles found", color=(140, 140, 140))

            with dpg.group(horizontal=True):
                dpg.add_button(label="Refresh", callback=self._on_refresh)

            dpg.add_spacer(height=15)
            dpg.add_separator()
            dpg.add_spacer(height=10)

            # Manual entry section
            dpg.add_text("PRIVATE / NEW PROFILE")
            dpg.add_spacer(height=5)

            dpg.add_text("Name:", color=(180, 180, 180))
            dpg.add_input_text(tag="profile_name_input", width=-1, callback=self._on_manual_input)

            dpg.add_spacer(height=5)
            dpg.add_text("Password:", color=(180, 180, 180))
            dpg.add_input_text(tag="profile_password_input", password=True, width=-1)

            dpg.add_spacer(height=5)
            dpg.add_checkbox(label="Create new profile", tag="create_new_checkbox")

            dpg.add_spacer(height=20)

            # Buttons
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=150)
                dpg.add_button(label="Cancel", width=100, callback=self._on_cancel_click)
                dpg.add_button(label="Connect", width=100, callback=self._on_connect_click)

    def _on_profile_select(self, profile_name: str):
        """Handle public profile selection."""
        self.selected_profile = profile_name
        dpg.set_value("profile_name_input", profile_name)
        dpg.set_value("create_new_checkbox", False)

    def _on_manual_input(self, sender, app_data):
        """Handle manual profile name input."""
        self.selected_profile = None  # Clear radio selection

    def _on_refresh(self):
        """Refresh profile list."""
        self._fetch_profiles()
        # Recreate the dialog
        if dpg.does_item_exist("profile_dialog"):
            dpg.delete_item("profile_dialog")
        self._create_window()

    def _on_cancel_click(self):
        """Handle cancel button."""
        if dpg.does_item_exist("profile_dialog"):
            dpg.delete_item("profile_dialog")
        self.on_cancel()

    def _on_connect_click(self):
        """Handle connect button."""
        name = dpg.get_value("profile_name_input").strip()
        password = dpg.get_value("profile_password_input")
        is_new = dpg.get_value("create_new_checkbox")

        if not name:
            # Show error
            return

        if dpg.does_item_exist("profile_dialog"):
            dpg.delete_item("profile_dialog")

        self.on_select(name, password, is_new)

    def close(self):
        """Close the dialog."""
        if dpg.does_item_exist("profile_dialog"):
            dpg.delete_item("profile_dialog")
```

**Step 2: Commit**

```bash
git add bb_detector/ui/profile_dialog.py
git commit -m "feat: add profile selection dialog"
```

---

### Task 4: Create Play Tab

**Files:**
- Create: `bb_detector/ui/tabs/__init__.py`
- Create: `bb_detector/ui/tabs/play.py`

**Step 1: Create tabs package**

```python
# bb_detector/ui/tabs/__init__.py
"""Tab components for main window."""
from .play import PlayTab
from .settings import SettingsTab
from .calibration import CalibrationTab

__all__ = ['PlayTab', 'SettingsTab', 'CalibrationTab']
```

**Step 2: Create Play tab**

```python
# bb_detector/ui/tabs/play.py
"""Play tab - main gameplay controls."""
import dearpygui.dearpygui as dpg
from typing import Callable, Optional
from ..theme import COLORS, create_accent_button_theme, create_success_button_theme, create_boss_button_theme

class PlayTab:
    """Play tab with deaths, timer, and boss controls."""

    def __init__(
        self,
        on_manual_death: Callable[[], None],
        on_timer_start: Callable[[], None],
        on_timer_stop: Callable[[], None],
        on_timer_reset: Callable[[], None],
        on_boss_start: Callable[[], None],
        on_boss_victory: Callable[[str], None],
        on_boss_cancel: Callable[[], None],
        on_toggle_detection: Callable[[], None],
    ):
        self.on_manual_death = on_manual_death
        self.on_timer_start = on_timer_start
        self.on_timer_stop = on_timer_stop
        self.on_timer_reset = on_timer_reset
        self.on_boss_start = on_boss_start
        self.on_boss_victory = on_boss_victory
        self.on_boss_cancel = on_boss_cancel
        self.on_toggle_detection = on_toggle_detection

        self._accent_theme = None
        self._success_theme = None
        self._boss_theme = None

    def create(self, parent: int):
        """Create the Play tab content."""
        self._accent_theme = create_accent_button_theme()
        self._success_theme = create_success_button_theme()
        self._boss_theme = create_boss_button_theme()

        with dpg.tab(label="Play", parent=parent):
            dpg.add_spacer(height=10)

            # Deaths section
            dpg.add_text("DEATHS", color=COLORS['text_dim'])
            dpg.add_spacer(height=5)

            with dpg.child_window(height=80, border=True):
                dpg.add_spacer(height=10)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=20)
                    dpg.add_text("0", tag="deaths_display", color=COLORS['accent'])
                    # Make text large via font (handled in app.py)

                dpg.add_spacer(height=10)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=20)
                    btn = dpg.add_button(label="+ Manual Death", callback=self._on_death_click, width=150)
                    dpg.bind_item_theme(btn, self._accent_theme)

            dpg.add_spacer(height=15)

            # Timer section
            with dpg.group(horizontal=True):
                dpg.add_text("TIMER", color=COLORS['text_dim'])
                dpg.add_spacer(width=20)
                dpg.add_text("00:00:00", tag="timer_display")

            dpg.add_spacer(height=5)
            with dpg.group(horizontal=True):
                btn_start = dpg.add_button(label="Start", tag="timer_start_btn", callback=self._on_timer_start, width=80)
                dpg.bind_item_theme(btn_start, self._success_theme)
                btn_stop = dpg.add_button(label="Stop", tag="timer_stop_btn", callback=self._on_timer_stop, width=80)
                dpg.add_button(label="Reset", callback=self._on_timer_reset, width=80)

            dpg.add_spacer(height=15)
            dpg.add_separator()
            dpg.add_spacer(height=10)

            # Boss mode section
            with dpg.group(horizontal=True):
                dpg.add_text("BOSS MODE", color=COLORS['text_dim'])
                dpg.add_spacer(width=10)
                dpg.add_text("OFF", tag="boss_status", color=COLORS['text_dim'])

            dpg.add_spacer(height=5)

            with dpg.child_window(height=100, border=True, tag="boss_section"):
                dpg.add_spacer(height=5)

                with dpg.group(horizontal=True):
                    dpg.add_text("Boss Deaths:", color=COLORS['text_dim'])
                    dpg.add_text("0", tag="boss_deaths_display", color=COLORS['boss'])

                dpg.add_spacer(height=10)

                with dpg.group(horizontal=True, tag="boss_buttons_inactive"):
                    btn_boss = dpg.add_button(label="Start Boss", callback=self._on_boss_start, width=120)
                    dpg.bind_item_theme(btn_boss, self._boss_theme)

                with dpg.group(horizontal=True, tag="boss_buttons_active", show=False):
                    btn_victory = dpg.add_button(label="Victory", callback=self._on_boss_victory_click, width=100)
                    dpg.bind_item_theme(btn_victory, self._success_theme)
                    btn_cancel = dpg.add_button(label="Cancel", callback=self._on_boss_cancel, width=100)

            dpg.add_spacer(height=15)
            dpg.add_separator()
            dpg.add_spacer(height=10)

            # Detection toggle
            with dpg.group(horizontal=True):
                dpg.add_text("Detection:", color=COLORS['text_dim'])
                dpg.add_spacer(width=5)
                dpg.add_text("ON", tag="detection_status", color=COLORS['success'])
                dpg.add_spacer(width=20)
                dpg.add_button(label="Toggle", callback=self._on_toggle_detection, width=80)

    def update(self, deaths: int, elapsed: int, is_running: bool,
               boss_mode: bool, boss_deaths: int, detection_enabled: bool):
        """Update all displays."""
        # Deaths
        if dpg.does_item_exist("deaths_display"):
            dpg.set_value("deaths_display", str(deaths))

        # Timer
        if dpg.does_item_exist("timer_display"):
            hours = elapsed // 3600000
            minutes = (elapsed % 3600000) // 60000
            seconds = (elapsed % 60000) // 1000
            dpg.set_value("timer_display", f"{hours:02d}:{minutes:02d}:{seconds:02d}")

        # Timer buttons
        if dpg.does_item_exist("timer_start_btn"):
            dpg.configure_item("timer_start_btn", enabled=not is_running)
        if dpg.does_item_exist("timer_stop_btn"):
            dpg.configure_item("timer_stop_btn", enabled=is_running)

        # Boss mode
        if dpg.does_item_exist("boss_status"):
            if boss_mode:
                dpg.set_value("boss_status", "ACTIVE")
                dpg.configure_item("boss_status", color=COLORS['boss'])
            else:
                dpg.set_value("boss_status", "OFF")
                dpg.configure_item("boss_status", color=COLORS['text_dim'])

        if dpg.does_item_exist("boss_deaths_display"):
            dpg.set_value("boss_deaths_display", str(boss_deaths))

        if dpg.does_item_exist("boss_buttons_inactive"):
            dpg.configure_item("boss_buttons_inactive", show=not boss_mode)
        if dpg.does_item_exist("boss_buttons_active"):
            dpg.configure_item("boss_buttons_active", show=boss_mode)

        # Detection
        if dpg.does_item_exist("detection_status"):
            if detection_enabled:
                dpg.set_value("detection_status", "ON")
                dpg.configure_item("detection_status", color=COLORS['success'])
            else:
                dpg.set_value("detection_status", "OFF")
                dpg.configure_item("detection_status", color=COLORS['accent'])

    def _on_death_click(self):
        self.on_manual_death()

    def _on_timer_start(self):
        self.on_timer_start()

    def _on_timer_stop(self):
        self.on_timer_stop()

    def _on_timer_reset(self):
        self.on_timer_reset()

    def _on_boss_start(self):
        self.on_boss_start()

    def _on_boss_victory_click(self):
        """Show victory dialog to enter boss name."""
        with dpg.window(
            label="Boss Victory",
            modal=True,
            width=300,
            height=120,
            pos=[100, 200],
            tag="victory_dialog",
            no_resize=True
        ):
            dpg.add_text("Enter boss name:")
            dpg.add_input_text(tag="boss_name_input", width=-1)
            dpg.add_spacer(height=10)
            with dpg.group(horizontal=True):
                dpg.add_button(label="Cancel", callback=lambda: dpg.delete_item("victory_dialog"), width=100)
                dpg.add_button(label="Confirm", callback=self._on_victory_confirm, width=100)

    def _on_victory_confirm(self):
        name = dpg.get_value("boss_name_input") if dpg.does_item_exist("boss_name_input") else ""
        if dpg.does_item_exist("victory_dialog"):
            dpg.delete_item("victory_dialog")
        self.on_boss_victory(name)

    def _on_boss_cancel(self):
        self.on_boss_cancel()

    def _on_toggle_detection(self):
        self.on_toggle_detection()
```

**Step 3: Commit**

```bash
mkdir -p bb_detector/ui/tabs
git add bb_detector/ui/tabs/__init__.py bb_detector/ui/tabs/play.py
git commit -m "feat: add Play tab with deaths, timer, boss controls"
```

---

### Task 5: Create Settings Tab

**Files:**
- Create: `bb_detector/ui/tabs/settings.py`

**Step 1: Write implementation**

```python
# bb_detector/ui/tabs/settings.py
"""Settings tab - configuration options."""
import dearpygui.dearpygui as dpg
from typing import Callable, Dict, Any, List
from ..theme import COLORS

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
            with dpg.group(horizontal=True):
                dpg.add_text("Monitor:", color=COLORS['text_dim'], indent=10)
                dpg.add_combo(
                    items=["Display 1", "Display 2", "Display 3"],
                    default_value="Display 1",
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
```

**Step 2: Commit**

```bash
git add bb_detector/ui/tabs/settings.py
git commit -m "feat: add Settings tab with profile, detection, hotkeys config"
```

---

### Task 6: Create Calibration Tab

**Files:**
- Create: `bb_detector/ui/tabs/calibration.py`

**Step 1: Write implementation**

```python
# bb_detector/ui/tabs/calibration.py
"""Calibration tab - template selection and detection testing."""
import dearpygui.dearpygui as dpg
from typing import Callable, Optional
from pathlib import Path
import numpy as np
from ..theme import COLORS

class CalibrationTab:
    """Calibration tab for template selection and detection testing."""

    TEMPLATES = [
        ("YOU DIED (English)", "you_died_en.png"),
        ("ТЫ МЕРТВ (Russian)", "you_died_ru.png"),
        ("Custom...", None),
    ]

    def __init__(
        self,
        on_template_change: Callable[[str], None],
        on_capture: Callable[[], np.ndarray],
        on_test_detection: Callable[[np.ndarray], tuple],
    ):
        self.on_template_change = on_template_change
        self.on_capture = on_capture
        self.on_test_detection = on_test_detection
        self._captured_frame: Optional[np.ndarray] = None
        self._texture_id: Optional[int] = None

    def create(self, parent: int):
        """Create the Calibration tab content."""
        with dpg.tab(label="Calibration", parent=parent):
            dpg.add_spacer(height=10)

            # Template section
            dpg.add_text("DEATH TEMPLATE", color=COLORS['text_dim'])
            dpg.add_spacer(height=5)

            # Template preview placeholder
            with dpg.child_window(height=80, border=True, tag="template_preview_window"):
                dpg.add_text("Template preview", color=COLORS['text_dim'])

            dpg.add_spacer(height=10)

            # Template selector
            with dpg.group(horizontal=True):
                dpg.add_text("Template:", color=COLORS['text_dim'])
                dpg.add_combo(
                    items=[t[0] for t in self.TEMPLATES],
                    default_value=self.TEMPLATES[0][0],
                    tag="template_selector",
                    width=200,
                    callback=self._on_template_select
                )

            dpg.add_spacer(height=15)
            dpg.add_separator()
            dpg.add_spacer(height=10)

            # Test detection section
            dpg.add_text("TEST DETECTION", color=COLORS['text_dim'])
            dpg.add_spacer(height=10)

            dpg.add_button(label="Capture Screen", callback=self._on_capture, width=150)

            dpg.add_spacer(height=10)

            # Captured frame preview
            with dpg.child_window(height=150, border=True, tag="capture_preview_window"):
                dpg.add_text("No capture", tag="capture_status", color=COLORS['text_dim'])
                dpg.add_spacer(height=10)
                dpg.add_text("Result: -", tag="detection_result", color=COLORS['text_dim'])

            dpg.add_spacer(height=10)

            with dpg.group(horizontal=True):
                dpg.add_button(label="Test Now", callback=self._on_test, width=100)
                dpg.add_button(label="Load Image", callback=self._on_load_image, width=100)

    def _on_template_select(self, sender, app_data):
        """Handle template selection."""
        selected = app_data

        # Find the template file
        template_file = None
        for name, file in self.TEMPLATES:
            if name == selected:
                template_file = file
                break

        if template_file is None:
            # Custom - open file dialog
            self._open_file_dialog()
        else:
            self.on_template_change(template_file)

    def _open_file_dialog(self):
        """Open file dialog for custom template."""
        # DearPyGui file dialog
        with dpg.file_dialog(
            directory_selector=False,
            show=True,
            callback=self._on_file_selected,
            width=500,
            height=400
        ):
            dpg.add_file_extension(".png")
            dpg.add_file_extension(".jpg")
            dpg.add_file_extension(".jpeg")

    def _on_file_selected(self, sender, app_data):
        """Handle custom file selection."""
        if app_data and 'file_path_name' in app_data:
            file_path = app_data['file_path_name']
            self.on_template_change(file_path)

    def _on_capture(self):
        """Capture current screen."""
        frame = self.on_capture()
        if frame is not None:
            self._captured_frame = frame
            self._update_capture_preview()

    def _update_capture_preview(self):
        """Update capture preview display."""
        if self._captured_frame is not None:
            if dpg.does_item_exist("capture_status"):
                h, w = self._captured_frame.shape[:2]
                dpg.set_value("capture_status", f"Captured: {w}x{h}")

    def _on_test(self):
        """Test detection on captured frame."""
        if self._captured_frame is None:
            if dpg.does_item_exist("detection_result"):
                dpg.set_value("detection_result", "Result: No capture to test")
            return

        is_match, confidence = self.on_test_detection(self._captured_frame)

        if dpg.does_item_exist("detection_result"):
            if is_match:
                dpg.set_value("detection_result", f"Result: MATCH ({confidence:.2f})")
                dpg.configure_item("detection_result", color=COLORS['success'])
            else:
                dpg.set_value("detection_result", f"Result: No match ({confidence:.2f})")
                dpg.configure_item("detection_result", color=COLORS['accent'])

    def _on_load_image(self):
        """Load image from file for testing."""
        with dpg.file_dialog(
            directory_selector=False,
            show=True,
            callback=self._on_test_image_selected,
            width=500,
            height=400
        ):
            dpg.add_file_extension(".png")
            dpg.add_file_extension(".jpg")
            dpg.add_file_extension(".jpeg")

    def _on_test_image_selected(self, sender, app_data):
        """Handle test image file selection."""
        if app_data and 'file_path_name' in app_data:
            import cv2
            file_path = app_data['file_path_name']
            frame = cv2.imread(file_path)
            if frame is not None:
                # Convert BGR to RGB
                self._captured_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self._update_capture_preview()
```

**Step 2: Update tabs __init__.py**

```python
# bb_detector/ui/tabs/__init__.py
"""Tab components for main window."""
from .play import PlayTab
from .settings import SettingsTab
from .calibration import CalibrationTab

__all__ = ['PlayTab', 'SettingsTab', 'CalibrationTab']
```

**Step 3: Commit**

```bash
git add bb_detector/ui/tabs/calibration.py bb_detector/ui/tabs/__init__.py
git commit -m "feat: add Calibration tab with template selection and test"
```

---

### Task 7: Create Compact Mode Window

**Files:**
- Create: `bb_detector/ui/compact.py`

**Step 1: Write implementation**

```python
# bb_detector/ui/compact.py
"""Compact mode window - minimal overlay during gameplay."""
import dearpygui.dearpygui as dpg
from typing import Callable
from .theme import COLORS

class CompactWindow:
    """Compact overlay window showing essential info during gameplay."""

    WIDTH = 300
    HEIGHT = 60

    def __init__(self, on_expand: Callable[[], None]):
        self.on_expand = on_expand
        self._visible = False
        self._position = [50, 50]

    def create(self):
        """Create the compact window (hidden initially)."""
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
            with dpg.group(horizontal=True):
                # Deaths
                dpg.add_text("", tag="compact_deaths", color=COLORS['accent'])
                dpg.add_spacer(width=15)

                # Timer
                dpg.add_text("", tag="compact_timer")

            with dpg.group(horizontal=True):
                # Boss info
                dpg.add_text("", tag="compact_boss", color=COLORS['boss'])
                dpg.add_spacer(width=15)

                # Status
                dpg.add_text("", tag="compact_status", color=COLORS['success'])

        # Click handler to expand
        with dpg.item_handler_registry(tag="compact_click_handler"):
            dpg.add_item_clicked_handler(callback=self._on_click)

        dpg.bind_item_handler_registry("compact_window", "compact_click_handler")

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
               boss_deaths: int, connected: bool, profile: str):
        """Update compact display."""
        # Deaths
        if dpg.does_item_exist("compact_deaths"):
            dpg.set_value("compact_deaths", f"Deaths: {deaths}")

        # Timer
        if dpg.does_item_exist("compact_timer"):
            hours = elapsed // 3600000
            minutes = (elapsed % 3600000) // 60000
            seconds = (elapsed % 60000) // 1000
            dpg.set_value("compact_timer", f"{hours:02d}:{minutes:02d}:{seconds:02d}")

        # Boss
        if dpg.does_item_exist("compact_boss"):
            if boss_mode:
                dpg.set_value("compact_boss", f"Boss: {boss_deaths}")
            else:
                dpg.set_value("compact_boss", "")

        # Status
        if dpg.does_item_exist("compact_status"):
            if connected:
                dpg.set_value("compact_status", f"{profile}")
                dpg.configure_item("compact_status", color=COLORS['success'])
            else:
                dpg.set_value("compact_status", "Offline")
                dpg.configure_item("compact_status", color=COLORS['accent'])

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

    def _on_click(self, sender, app_data):
        """Handle click on compact window."""
        # Double-click to expand
        if app_data == 1:  # Left click
            self.on_expand()
```

**Step 2: Commit**

```bash
git add bb_detector/ui/compact.py
git commit -m "feat: add compact mode window for gameplay"
```

---

### Task 8: Create Main App Window

**Files:**
- Create: `bb_detector/ui/app.py`

**Step 1: Write implementation**

```python
# bb_detector/ui/app.py
"""Main application window with tabs."""
import dearpygui.dearpygui as dpg
from typing import Optional, Callable
import asyncio

from .theme import create_theme, COLORS
from .tabs.play import PlayTab
from .tabs.settings import SettingsTab
from .tabs.calibration import CalibrationTab
from .compact import CompactWindow
from .profile_dialog import ProfileDialog
from ..state import StateManager
from ..config import Config

class App:
    """Main application window manager."""

    FULL_WIDTH = 400
    FULL_HEIGHT = 520

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
        on_boss_victory: Callable,
        on_boss_cancel: Callable,
        on_toggle_detection: Callable,
        on_profile_select: Callable,
        on_template_change: Callable,
        on_capture: Callable,
        on_test_detection: Callable,
        on_quit: Callable,
    ):
        self.config = config
        self.state = state

        # Store callbacks
        self._on_manual_death = on_manual_death
        self._on_timer_start = on_timer_start
        self._on_timer_stop = on_timer_stop
        self._on_timer_reset = on_timer_reset
        self._on_boss_start = on_boss_start
        self._on_boss_victory = on_boss_victory
        self._on_boss_cancel = on_boss_cancel
        self._on_toggle_detection = on_toggle_detection
        self._on_profile_select = on_profile_select
        self._on_template_change = on_template_change
        self._on_capture = on_capture
        self._on_test_detection = on_test_detection
        self._on_quit = on_quit

        # UI components
        self.play_tab: Optional[PlayTab] = None
        self.settings_tab: Optional[SettingsTab] = None
        self.calibration_tab: Optional[CalibrationTab] = None
        self.compact_window: Optional[CompactWindow] = None

        self._is_compact = False
        self._running = False

    def init(self):
        """Initialize DearPyGui and create windows."""
        dpg.create_context()

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
        """Create the main window with tabs."""
        with dpg.window(tag="main_window", label="", no_title_bar=True, no_resize=True, no_move=True):
            # Configure to fill viewport
            dpg.set_primary_window("main_window", True)

            # Header
            with dpg.group(horizontal=True):
                dpg.add_text("BB Death Detector", color=COLORS['text'])
                dpg.add_spacer(width=100)
                dpg.add_button(label="[_]", width=30, callback=self._switch_to_compact)
                dpg.add_button(label="[X]", width=30, callback=self._on_quit)

            dpg.add_separator()
            dpg.add_spacer(height=5)

            # Tab bar
            with dpg.tab_bar(tag="main_tabs"):
                # Play tab
                self.play_tab = PlayTab(
                    on_manual_death=self._on_manual_death,
                    on_timer_start=self._on_timer_start,
                    on_timer_stop=self._on_timer_stop,
                    on_timer_reset=self._on_timer_reset,
                    on_boss_start=self._on_boss_start,
                    on_boss_victory=self._on_boss_victory,
                    on_boss_cancel=self._on_boss_cancel,
                    on_toggle_detection=self._on_toggle_detection,
                )
                self.play_tab.create("main_tabs")

                # Settings tab
                self.settings_tab = SettingsTab(
                    config=self.config,
                    on_change_profile=self._show_profile_dialog,
                    on_save_settings=self._save_settings,
                )
                self.settings_tab.create("main_tabs")

                # Calibration tab
                self.calibration_tab = CalibrationTab(
                    on_template_change=self._on_template_change,
                    on_capture=self._on_capture,
                    on_test_detection=self._on_test_detection,
                )
                self.calibration_tab.create("main_tabs")

            # Footer - status bar
            dpg.add_spacer(height=5)
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_text("", tag="status_indicator", color=COLORS['accent'])
                dpg.add_text("Disconnected", tag="status_text", color=COLORS['text_dim'])

    def show_profile_dialog(self):
        """Show profile selection dialog."""
        dialog = ProfileDialog(
            on_select=self._on_profile_selected,
            on_cancel=self._on_profile_cancel
        )
        dialog.show()

    def _show_profile_dialog(self):
        """Internal: show profile dialog from settings."""
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

    def _on_state_change(self, key: str, value):
        """Handle state changes."""
        # Update UI based on state
        self._update_ui()

    def _update_ui(self):
        """Update all UI elements from state."""
        # Update play tab
        if self.play_tab:
            self.play_tab.update(
                deaths=self.state.deaths,
                elapsed=self.state.elapsed,
                is_running=self.state.is_running,
                boss_mode=self.state.boss_mode,
                boss_deaths=self.state.boss_deaths,
                detection_enabled=self.state.detection_enabled,
            )

        # Update settings tab
        if self.settings_tab:
            self.settings_tab.update(
                profile=self.state.profile_display_name or self.state.profile,
                connected=self.state.connected,
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

        # Update status bar
        if dpg.does_item_exist("status_indicator"):
            if self.state.connected:
                dpg.set_value("status_indicator", "●")
                dpg.configure_item("status_indicator", color=COLORS['success'])
            else:
                dpg.set_value("status_indicator", "●")
                dpg.configure_item("status_indicator", color=COLORS['accent'])

        if dpg.does_item_exist("status_text"):
            if self.state.connected:
                profile = self.state.profile_display_name or self.state.profile or ""
                dpg.set_value("status_text", f"Connected: {profile}")
            else:
                dpg.set_value("status_text", "Disconnected")

    def render(self):
        """Render one frame."""
        if self._running:
            dpg.render_dearpygui_frame()

    def is_running(self) -> bool:
        """Check if app is still running."""
        return self._running and dpg.is_dearpygui_running()

    def destroy(self):
        """Cleanup and destroy DearPyGui context."""
        self._running = False
        dpg.destroy_context()
```

**Step 2: Commit**

```bash
git add bb_detector/ui/app.py
git commit -m "feat: add main application window with tabs and mode switching"
```

---

### Task 9: Integrate New UI with Main Module

**Files:**
- Modify: `bb_detector/main.py`

**Step 1: Rewrite main.py to use new UI**

```python
# bb_detector/main.py
"""BB Death Detector - Main application entry point."""
import asyncio
import signal
import time
from pathlib import Path

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
```

**Step 2: Commit**

```bash
git add bb_detector/main.py
git commit -m "feat: integrate new UI with main application"
```

---

### Task 10: Update Dependencies

**Files:**
- Modify: `requirements/base.txt`

**Step 1: Add requests dependency**

```text
# requirements/base.txt
mss>=9.0.0
opencv-python>=4.8.0
websockets>=12.0
pystray>=0.19.0
dearpygui>=1.11.0
pynput>=1.7.6
Pillow>=10.0.0
requests>=2.31.0
numpy>=1.26.0
```

**Step 2: Install and test**

Run: `cd /Users/warezzko/Desktop/netfl/bb-detector && source .venv/bin/activate && pip install requests`

**Step 3: Commit**

```bash
git add requirements/base.txt
git commit -m "chore: add requests to dependencies"
```

---

### Task 11: Delete Old Overlay Module

**Files:**
- Delete: `bb_detector/overlay.py`

**Step 1: Remove old overlay**

```bash
rm bb_detector/overlay.py
```

**Step 2: Commit**

```bash
git add -u bb_detector/overlay.py
git commit -m "refactor: remove old overlay module (replaced by ui/)"
```

---

### Task 12: Run Full Test and Verify

**Step 1: Run all tests**

Run: `cd /Users/warezzko/Desktop/netfl/bb-detector && source .venv/bin/activate && python -m pytest tests/ -v`

Expected: All tests pass

**Step 2: Run application manually**

Run: `cd /Users/warezzko/Desktop/netfl/bb-detector && source .venv/bin/activate && python -m bb_detector`

Expected:
- Application starts
- Profile dialog appears (if no profile configured)
- Main window with 3 tabs visible
- Compact mode toggle works

**Step 3: Final commit**

```bash
git add -A
git commit -m "feat: complete full UI implementation for BB Death Detector"
```

---

## Summary

| Task | Component | Status |
|------|-----------|--------|
| 1 | State Manager | [ ] |
| 2 | UI Theme | [ ] |
| 3 | Profile Dialog | [ ] |
| 4 | Play Tab | [ ] |
| 5 | Settings Tab | [ ] |
| 6 | Calibration Tab | [ ] |
| 7 | Compact Window | [ ] |
| 8 | Main App Window | [ ] |
| 9 | Main Integration | [ ] |
| 10 | Dependencies | [ ] |
| 11 | Remove Old Overlay | [ ] |
| 12 | Final Test | [ ] |
