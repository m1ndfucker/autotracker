# bb_detector/ui/theme.py
"""DearPyGui theme configuration - Refined dark theme inspired by Discord/Linear."""
import dearpygui.dearpygui as dpg

# ==============================================================================
# Color Palette - Modern dark theme with depth
# ==============================================================================

COLORS = {
    # Backgrounds - layered with subtle depth
    'bg_base': (17, 17, 21, 255),         # Deepest layer
    'bg_primary': (23, 23, 28, 255),      # Main window
    'bg_secondary': (30, 30, 36, 255),    # Cards/sections
    'bg_elevated': (38, 38, 46, 255),     # Hover/elevated
    'bg_input': (25, 25, 31, 255),        # Input fields

    # Text - proper contrast hierarchy
    'text_primary': (248, 248, 250, 255),   # Headings, important
    'text_secondary': (180, 180, 186, 255), # Body text
    'text_tertiary': (120, 120, 128, 255),  # Labels, muted
    'text_disabled': (80, 80, 86, 255),     # Disabled

    # Red (Deaths) - refined, less harsh
    'red': (220, 68, 68, 255),
    'red_hover': (235, 90, 90, 255),
    'red_active': (180, 55, 55, 255),
    'red_muted': (160, 50, 50, 255),

    # Green (Success/Connected)
    'green': (76, 191, 128, 255),
    'green_hover': (90, 210, 145, 255),
    'green_active': (60, 155, 100, 255),

    # Purple (Boss mode)
    'purple': (155, 120, 235, 255),
    'purple_hover': (175, 145, 255, 255),
    'purple_active': (130, 100, 200, 255),

    # Teal (Boss fights/Completed)
    'teal': (143, 186, 168, 255),
    'teal_hover': (163, 206, 188, 255),
    'teal_active': (106, 154, 136, 255),

    # Amber (Warning/Timer)
    'amber': (245, 180, 65, 255),

    # Borders - subtle but visible
    'border_subtle': (45, 45, 52, 255),
    'border_default': (55, 55, 62, 255),
    'border_strong': (70, 70, 78, 255),

    # Legacy aliases for compatibility
    'bg': (23, 23, 28, 255),
    'bg_hover': (38, 38, 46, 255),
    'accent': (220, 68, 68, 255),
    'accent_hover': (235, 90, 90, 255),
    'success': (76, 191, 128, 255),
    'boss': (155, 120, 235, 255),
    'text': (248, 248, 250, 255),
    'text_dim': (120, 120, 128, 255),
    'border': (55, 55, 62, 255),
    'warning': (245, 180, 65, 255),
}

# Spacing system (4px base grid)
SPACING = {
    'xs': 4,
    'sm': 8,
    'md': 16,
    'lg': 24,
    'xl': 32,
}


def create_theme() -> int:
    """Create the main application theme."""
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvAll):
            # === Window Backgrounds ===
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, COLORS['bg_primary'])
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, COLORS['bg_secondary'])
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, COLORS['bg_secondary'])
            dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, COLORS['bg_base'])

            # === Text ===
            dpg.add_theme_color(dpg.mvThemeCol_Text, COLORS['text_primary'])
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, COLORS['text_disabled'])

            # === Borders ===
            dpg.add_theme_color(dpg.mvThemeCol_Border, COLORS['border_default'])
            dpg.add_theme_color(dpg.mvThemeCol_BorderShadow, (0, 0, 0, 0))

            # === Frames (inputs, combo boxes) ===
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, COLORS['bg_input'])
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, COLORS['bg_elevated'])
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, COLORS['bg_secondary'])

            # === Buttons ===
            dpg.add_theme_color(dpg.mvThemeCol_Button, COLORS['bg_elevated'])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (50, 50, 58, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, COLORS['bg_secondary'])

            # === Headers/Tabs ===
            dpg.add_theme_color(dpg.mvThemeCol_Header, COLORS['bg_secondary'])
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, COLORS['bg_elevated'])
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, COLORS['red'])

            dpg.add_theme_color(dpg.mvThemeCol_Tab, COLORS['bg_secondary'])
            dpg.add_theme_color(dpg.mvThemeCol_TabHovered, COLORS['bg_elevated'])
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, COLORS['bg_primary'])
            dpg.add_theme_color(dpg.mvThemeCol_TabUnfocused, COLORS['bg_secondary'])
            dpg.add_theme_color(dpg.mvThemeCol_TabUnfocusedActive, COLORS['bg_primary'])

            # === Sliders ===
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, COLORS['red'])
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, COLORS['red_hover'])

            # === Checkbox ===
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, COLORS['red'])

            # === Separator ===
            dpg.add_theme_color(dpg.mvThemeCol_Separator, COLORS['border_subtle'])

            # === Scrollbar ===
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, COLORS['bg_primary'])
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, COLORS['bg_elevated'])
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, (60, 60, 70, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive, (70, 70, 80, 255))

            # === Rounding (modern, softer) ===
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 8)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 6)

            # === Sizing ===
            dpg.add_theme_style(dpg.mvStyleVar_GrabMinSize, 14)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize, 12)

            # === Padding & Spacing (compact) ===
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 4)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 4)
            dpg.add_theme_style(dpg.mvStyleVar_ItemInnerSpacing, 4, 2)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 10, 10)
            dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 4, 2)

            # === Borders ===
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 1)
            dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 1)

    return theme


def create_accent_button_theme() -> int:
    """Red primary action button."""
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, COLORS['red'])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, COLORS['red_hover'])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, COLORS['red_active'])
            dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255))
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 0)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
    return theme


def create_success_button_theme() -> int:
    """Green success button."""
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, COLORS['green'])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, COLORS['green_hover'])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, COLORS['green_active'])
            dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255))
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 0)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
    return theme


def create_boss_button_theme() -> int:
    """Purple boss mode button."""
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, COLORS['purple'])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, COLORS['purple_hover'])
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, COLORS['purple_active'])
            dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255))
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 0)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
    return theme


def create_ghost_button_theme() -> int:
    """Transparent/ghost button for window controls."""
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (0, 0, 0, 0))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (255, 255, 255, 20))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (255, 255, 255, 30))
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 0)
    return theme


def create_card_theme() -> int:
    """Elevated card/container theme."""
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvChildWindow):
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, COLORS['bg_secondary'])
            dpg.add_theme_color(dpg.mvThemeCol_Border, COLORS['border_subtle'])
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 8)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 16, 12)
    return theme
