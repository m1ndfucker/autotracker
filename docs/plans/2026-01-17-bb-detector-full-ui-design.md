# BB Death Detector - Full UI Design

**Date:** 2026-01-17
**Status:** Ready for implementation

---

## Overview

Redesign of BB Death Detector from minimal overlay to full-featured desktop application with unified main window.

**Key Changes from v1:**
- Single main window with tabs (instead of tray + minimal overlay)
- Full controls for timer, boss mode, calibration
- First-run profile selection wizard
- Compact mode for gameplay

---

## Window Architecture

### Two Modes

**Full Mode** (~400x500 px):
- Header: profile name + compact mode button
- Tabs: Play | Settings | Calibration
- Footer: connection status

**Compact Mode** (~300x80 px, always-on-top):
```
┌────────────────────────────┐
│ 💀 42  │ ⏱️ 02:34:15      │
│ ⚔️ Boss: 3  │ 🟢 warezz   │
└────────────────────────────┘
```
- Click → expand to full mode
- Hotkey `Ctrl+Shift+O` toggles modes
- Draggable, position saved to config

### Close Behavior

| Platform | Behavior |
|----------|----------|
| Windows | Minimize to system tray |
| macOS | Stay in Dock (no tray due to threading issues) |

**Tray/Dock Menu:** Show, Compact Mode, Quit

---

## Tab: Play

Main gameplay tab with all controls.

```
┌─────────────────────────────────────┐
│  DEATHS                             │
│  ┌─────────────────────────────┐    │
│  │         42                  │    │
│  └─────────────────────────────┘    │
│  [+ Manual Death]                   │
│                                     │
│  TIMER         ⏱️ 02:34:15          │
│  [▶ Start] [⏸ Stop] [↺ Reset]       │
│                                     │
│  ─────────────────────────────────  │
│  BOSS MODE                     OFF  │
│  ┌─────────────────────────────┐    │
│  │  Boss Deaths: 0             │    │
│  │  [⚔️ Start Boss]            │    │
│  │  [✓ Victory] [✗ Cancel]     │    │
│  └─────────────────────────────┘    │
│                                     │
│  Detection: ● ON    [Toggle]        │
└─────────────────────────────────────┘
```

**Elements:**
- Large death counter + manual add button
- Timer with controls (Start/Stop/Reset)
- Boss section: start, victory (with name input popup), cancel
- Auto-detection toggle

---

## Tab: Settings

Configuration for profile, detection, hotkeys, window.

```
┌─────────────────────────────────────┐
│  PROFILE                            │
│  ┌─────────────────────────────┐    │
│  │ Current: warezz        [✎]  │    │
│  │ Status: 🟢 Connected        │    │
│  └─────────────────────────────┘    │
│  [Change Profile]                   │
│                                     │
│  DETECTION                          │
│  ├─ Monitor:    [▼ Display 1   ]    │
│  ├─ FPS:        [▼ 10         ]     │
│  ├─ Threshold:  [====●====] 0.75    │
│  └─ Cooldown:   [▼ 5 sec      ]     │
│                                     │
│  HOTKEYS                            │
│  ├─ Manual Death:  [Ctrl+Shift+D]   │
│  ├─ Toggle Boss:   [Ctrl+Shift+B]   │
│  ├─ Toggle Mode:   [Ctrl+Shift+O]   │
│  └─ Pause Detect:  [Ctrl+Shift+P]   │
│                                     │
│  WINDOW                             │
│  ├─ □ Start minimized               │
│  ├─ □ Always on top (compact)       │
│  └─ Opacity: [========●=] 0.9       │
└─────────────────────────────────────┘
```

**Sections:**
- **Profile** - current profile, status, change button
- **Detection** - monitor, FPS, threshold, cooldown
- **Hotkeys** - editable (click → record combination)
- **Window** - behavior, opacity

---

## Tab: Calibration

Template selection and detection testing.

```
┌─────────────────────────────────────┐
│  DEATH TEMPLATE                     │
│                                     │
│  ┌─────────────────────────────┐    │
│  │  [Preview of template]      │    │
│  └─────────────────────────────┘    │
│                                     │
│  Template: [▼ YOU DIED (English)]   │
│            ○ YOU DIED (English)     │
│            ○ ТЫ МЕРТВ (Russian)     │
│            ○ Custom...              │
│                                     │
│  ─────────────────────────────────  │
│  TEST DETECTION                     │
│                                     │
│  [📷 Capture Screen]                │
│                                     │
│  ┌─────────────────────────────┐    │
│  │  [Last captured frame]      │    │
│  │  Result: ✓ MATCH (0.87)     │    │
│  └─────────────────────────────┘    │
│                                     │
│  [🎯 Test Now]  [📁 Load Image]     │
└─────────────────────────────────────┘
```

**Functions:**
- Template selection: built-in (EN/RU) or custom file
- Template preview
- Detection test: capture screen, test, load image
- Result: Match/No Match + confidence score

---

## First Run: Profile Selection

Modal window on first launch.

```
┌─────────────────────────────────────────┐
│         BB Death Detector               │
│         ─────────────────               │
│                                         │
│  Select or create a profile to start    │
│                                         │
│  PUBLIC PROFILES                        │
│  ┌─────────────────────────────────┐    │
│  │ ○ homius      (42 deaths)       │    │
│  │ ○ warezz      (156 deaths)      │    │
│  │ ○ streamer1   (89 deaths)       │    │
│  │                          [↻]    │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ── OR ──                               │
│                                         │
│  PRIVATE PROFILE                        │
│  Name:     [________________]           │
│  Password: [________________]           │
│                                         │
│  □ Create new profile                   │
│                                         │
│        [Cancel]  [Connect]              │
└─────────────────────────────────────────┘
```

**Logic:**
- Fetch public profiles list from server
- Select existing or enter manually
- "Create new" creates profile via API
- After selection → save to config, request password for auth
- Cancel = exit app (can't work without profile)

---

## Data Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ Screen      │────▶│ Detector     │────▶│ WebSocket   │
│ Capture     │     │ (OpenCV)     │     │ Client      │
│ (10 FPS)    │     │              │     │             │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                │
┌─────────────┐     ┌──────────────┐            │
│ Main UI     │◀────│ State        │◀───────────┘
│ (dearpygui) │     │ Manager      │
└─────────────┘     └──────────────┘
```

---

## Error Handling

| Situation | Behavior |
|-----------|----------|
| WS disconnect | Auto-reconnect every 3 sec, status "Reconnecting..." |
| Profile not found | Show profile selection dialog |
| Auth failed | Show error, request password again |
| Screen capture fail | Show warning, offer monitor selection |
| macOS permissions | Open System Preferences, show instructions |

---

## State Manager

Central state storage:
- `deaths: int`
- `elapsed: int` (ms)
- `isRunning: bool`
- `bossFightMode: bool`
- `bossDeaths: int`
- `connected: bool`
- `profile: str`
- `canEdit: bool`

UI subscribes to state changes. WebSocket updates state on `bb-state` messages.

---

## File Structure (New/Modified)

```
bb_detector/
├── main.py              # Modified - new UI architecture
├── ui/
│   ├── __init__.py
│   ├── app.py           # Main application window
│   ├── tabs/
│   │   ├── __init__.py
│   │   ├── play.py      # Play tab
│   │   ├── settings.py  # Settings tab
│   │   └── calibration.py # Calibration tab
│   ├── compact.py       # Compact mode window
│   ├── profile_dialog.py # Profile selection modal
│   └── theme.py         # DearPyGui theme/styling
├── state.py             # State manager
├── overlay.py           # REMOVED (replaced by ui/)
└── tray.py              # Modified - simplified
```

---

## Implementation Notes

1. **macOS**: No tray icon, only Dock. Solves main thread conflict.
2. **Single dearpygui context**: Both full and compact modes in same context.
3. **Mode switching**: Hide/show viewports, not recreate.
4. **Hotkey recording**: Use pynput listener in "record mode".
5. **Image preview**: Use dearpygui texture system for template/capture preview.
