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
