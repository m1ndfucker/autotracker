# BB Death Detector - Design Document

**Date:** 2026-01-17
**Status:** Ready for implementation

---

## Overview

**Name:** BB Death Detector
**Purpose:** Automatic death counter for Bloodborne via screen capture detection
**Platforms:** Windows, macOS
**Use case:** Playing on console via capture card or on PC

---

## Features

| Feature | Description |
|---------|-------------|
| **Auto death detection** | Template matching + color detection of "YOU DIED" / "ТЫ МЕРТВ" |
| **Manual death** | Hotkey `Ctrl+Shift+D` |
| **Boss Mode** | Fully manual: start/pause/victory/cancel via menu (`Ctrl+Shift+B`) |
| **Overlay** | Small always-on-top window: deaths, boss mode, status |
| **System Tray** | Tray icon with settings menu |
| **Calibration** | First-run wizard + built-in templates |
| **Profiles** | Select from public list + manual entry for private |

---

## Tech Stack

| Component | Windows | macOS | Library |
|-----------|---------|-------|---------|
| Screen capture | DirectX | CoreGraphics | `bettercam` / `mss` |
| Detection | — | — | `opencv-python` |
| WebSocket | — | — | `websockets` |
| Hotkeys | Win32 | Quartz | `pynput` |
| System Tray | Shell | AppKit | `pystray` |
| UI/Overlay | DirectX11 | Metal | `dearpygui` |

---

## Project Structure

```
bb-detector/
├── bb_detector/
│   ├── __init__.py
│   ├── main.py              # Entry point, main loop
│   ├── capture.py           # Cross-platform screen capture
│   ├── detector.py          # Template matching + color detection
│   ├── websocket_client.py  # WebSocket connection
│   ├── overlay.py           # Overlay window (dearpygui)
│   ├── tray.py              # System tray (pystray)
│   ├── hotkeys.py           # Global hotkeys (pynput)
│   ├── calibration.py       # Calibration wizard
│   ├── config.py            # Config load/save
│   ├── settings.py          # Settings window
│   ├── profile_selector.py  # Profile selection window
│   ├── boss_menu.py         # Boss control menu
│   └── platform_utils.py    # macOS permissions etc.
│
├── assets/
│   ├── templates/
│   │   ├── you_died_en.png
│   │   └── you_died_ru.png
│   ├── icon.ico             # Windows
│   ├── icon.icns            # macOS
│   ├── icon_active.png
│   └── icon_inactive.png
│
├── requirements/
│   ├── base.txt
│   ├── windows.txt
│   └── macos.txt
│
├── build/
│   ├── build_windows.py     # PyInstaller
│   └── build_macos.py       # py2app
│
├── config.json
├── build.py
├── Makefile
└── README.md
```

---

## Config Format (config.json)

```json
{
  "profile": {
    "name": "warezz",
    "password": "encrypted:...",
    "auto_connect": true
  },
  "detection": {
    "fps": 10,
    "death_cooldown": 5.0,
    "death_threshold": 0.75,
    "monitor": 0
  },
  "templates": {
    "death": {
      "builtin": "you_died_en.png",
      "custom": null
    }
  },
  "hotkeys": {
    "manual_death": "ctrl+shift+d",
    "toggle_boss": "ctrl+shift+b",
    "toggle_detection": "ctrl+shift+p",
    "show_overlay": "ctrl+shift+o"
  },
  "overlay": {
    "enabled": true,
    "position": [50, 50],
    "opacity": 0.85,
    "scale": 1.0
  },
  "calibration": {
    "completed": false
  }
}
```

---

## WebSocket API

| Action | Message |
|--------|---------|
| Auth | `{ type: 'bb-auth', password: '...' }` |
| Death | `{ type: 'bb-death' }` |
| Boss death | `{ type: 'bb-boss-death' }` |
| Boss start | `{ type: 'bb-boss-start' }` |
| Boss pause | `{ type: 'bb-boss-pause' }` |
| Boss resume | `{ type: 'bb-boss-resume' }` |
| Boss victory | `{ type: 'bb-boss-victory', name: '...' }` |
| Boss cancel | `{ type: 'bb-boss-cancel' }` |

**Endpoint:** `wss://watch.home.kg/ws?bloodborne=true&profile={name}`

---

## Hotkeys

| Combo | Action |
|-------|--------|
| `Ctrl+Shift+D` | Manual death |
| `Ctrl+Shift+B` | Boss menu |
| `Ctrl+Shift+P` | Toggle detection |
| `Ctrl+Shift+O` | Toggle overlay |

*On macOS: `Cmd` instead of `Ctrl`*

---

## Application Flow

```
Start
  │
  ├─► [macOS] Check permissions
  │      Screen Recording + Accessibility
  │
  ├─► Load config
  │
  ├─► [First run] Calibration
  │      1. Capture death screen
  │      2. Select "YOU DIED" region
  │      3. Test detection
  │
  ├─► Select profile
  │      Public list + manual entry
  │
  ├─► Initialize components
  │      Capture, Detector, WebSocket, Overlay, Tray, Hotkeys
  │
  └─► Main loop
        │
        ├─► Capture frame (10 FPS)
        ├─► Detect death
        │      └─► WebSocket: bb-death / bb-boss-death
        ├─► Update Overlay
        └─► Process WebSocket
```

---

## macOS Permissions

| Permission | Purpose | Where to enable |
|------------|---------|-----------------|
| Screen Recording | Screen capture | System Preferences → Privacy |
| Accessibility | Global hotkeys | System Preferences → Privacy |

---

## Build

| Platform | Tool | Output |
|----------|------|--------|
| Windows | PyInstaller | `BBDetector.exe` (~50-80 MB) |
| macOS | py2app | `BB Death Detector.app` → `.dmg` |

**CI/CD:** GitHub Actions auto-build on tag `v*`

---

## Implementation Plan

### Phase 1: Core Infrastructure
1. [ ] Project setup (directories, requirements, config)
2. [ ] `config.py` - Config management with encryption
3. [ ] `platform_utils.py` - macOS permissions check
4. [ ] `capture.py` - Cross-platform screen capture

### Phase 2: Detection
5. [ ] `detector.py` - Template matching + color detection
6. [ ] Built-in templates (you_died_en.png, you_died_ru.png)
7. [ ] `calibration.py` - Calibration wizard

### Phase 3: Networking
8. [ ] `websocket_client.py` - WebSocket with auto-reconnect

### Phase 4: UI
9. [ ] `overlay.py` - Overlay window with dearpygui
10. [ ] `tray.py` - System tray with pystray
11. [ ] `hotkeys.py` - Global hotkeys with pynput
12. [ ] `boss_menu.py` - Boss control menu
13. [ ] `profile_selector.py` - Profile selection
14. [ ] `settings.py` - Settings window

### Phase 5: Integration
15. [ ] `main.py` - Main application loop
16. [ ] Error handling and logging

### Phase 6: Build & Release
17. [ ] `build_windows.py` - PyInstaller config
18. [ ] `build_macos.py` - py2app config
19. [ ] GitHub Actions workflow
20. [ ] README.md

---

## Key Code Snippets

### Screen Capture (capture.py)

```python
class ScreenCapture:
    def __init__(self, monitor: int = 0, fps: int = 10):
        self.system = platform.system()
        if self.system == 'Windows':
            try:
                import bettercam
                self._backend = 'bettercam'
                self._camera = bettercam.create(output_idx=monitor)
            except ImportError:
                self._init_mss(monitor)
        else:
            self._init_mss(monitor)

    def _init_mss(self, monitor):
        import mss
        self._backend = 'mss'
        self._sct = mss.mss()
        self._monitor_info = self._sct.monitors[monitor + 1]

    def grab(self) -> np.ndarray | None:
        if self._backend == 'bettercam':
            return self._camera.get_latest_frame()
        elif self._backend == 'mss':
            screenshot = self._sct.grab(self._monitor_info)
            frame = np.array(screenshot)[:, :, :3][:, :, ::-1]
            return frame
```

### Death Detection (detector.py)

```python
class DeathDetector:
    def __init__(self, config):
        self.threshold = config.get('detection.death_threshold', 0.75)
        self._load_template(config)

    def check_death(self, frame: np.ndarray) -> tuple[bool, float]:
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        result = cv2.matchTemplate(gray_frame, self.template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        return max_val > self.threshold, max_val
```

### WebSocket Client (websocket_client.py)

```python
class BBWebSocket:
    def __init__(self, profile: str, password: str, on_state, on_connect, on_disconnect):
        self.url = f"wss://watch.home.kg/ws?bloodborne=true&profile={profile}"
        self.password = password
        self.authenticated = False
        # callbacks...

    async def connect(self):
        self.ws = await websockets.connect(self.url)
        asyncio.create_task(self._listen())

    async def send_death(self):
        if self.authenticated:
            await self.ws.send(json.dumps({'type': 'bb-death'}))
```

### Global Hotkeys (hotkeys.py)

```python
class GlobalHotkeys:
    def __init__(self):
        self.hotkeys: Dict[frozenset, Callable] = {}
        self.current_keys: Set[str] = set()

    def register(self, keys: str, callback: Callable):
        key_set = frozenset(k.strip().lower().replace('cmd', 'ctrl')
                           for k in keys.split('+'))
        self.hotkeys[key_set] = callback

    def start(self):
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()
```
