# bb_detector/ui/profile_dialog.py
"""Profile selection dialog for first run and profile changes."""
import dearpygui.dearpygui as dpg
from typing import Callable, List, Dict, Optional
import requests

class ProfileDialog:
    """Modal dialog for selecting or creating a profile."""

    API_URL = "https://soulsdeaths.somework.dev/api/bb-profiles"

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
        self._profile_map: Dict[str, str] = {}  # Map display text to profile name

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
                    profile_items = []
                    self._profile_map = {}  # Reset map
                    for profile in self.profiles[:10]:  # Limit to 10
                        name = profile.get('name', '')
                        display = profile.get('displayName', name)
                        deaths = profile.get('deaths', 0)
                        item_text = f"{display} ({deaths} deaths)"
                        profile_items.append(item_text)
                        self._profile_map[item_text] = name

                    dpg.add_radio_button(
                        items=profile_items,
                        tag="profile_radio_group",
                        callback=self._on_profile_radio_select
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

            dpg.add_spacer(height=10)
            dpg.add_text("Profile name is required", tag="profile_error_text", color=(220, 70, 70), show=False)

            dpg.add_spacer(height=10)

            # Buttons
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=150)
                dpg.add_button(label="Cancel", width=100, callback=self._on_cancel_click)
                dpg.add_button(label="Connect", width=100, callback=self._on_connect_click)

    def _on_profile_radio_select(self, sender, app_data):
        """Handle public profile radio selection."""
        if app_data in self._profile_map:
            profile_name = self._profile_map[app_data]
            self.selected_profile = profile_name
            dpg.set_value("profile_name_input", profile_name)
            dpg.set_value("create_new_checkbox", False)
            # Hide error if visible
            if dpg.does_item_exist("profile_error_text"):
                dpg.configure_item("profile_error_text", show=False)

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
            # Show error message
            if dpg.does_item_exist("profile_error_text"):
                dpg.configure_item("profile_error_text", show=True)
            return

        if dpg.does_item_exist("profile_dialog"):
            dpg.delete_item("profile_dialog")

        self.on_select(name, password, is_new)

    def close(self):
        """Close the dialog."""
        if dpg.does_item_exist("profile_dialog"):
            dpg.delete_item("profile_dialog")
