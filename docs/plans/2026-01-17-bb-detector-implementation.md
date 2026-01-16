# BB Death Detector Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a cross-platform Python application that auto-detects Bloodborne deaths via screen capture and syncs with the Bloodborne tracker server.

**Architecture:** Screen capture (bettercam/mss) → OpenCV template matching → WebSocket sync to watch.home.kg. System tray for background operation, dearpygui overlay for status display, pynput for global hotkeys.

**Tech Stack:** Python 3.12, mss, opencv-python, websockets, pystray, dearpygui, pynput

---

## Phase 1: Project Setup

### Task 1: Create Project Structure

**Files:**
- Create: `bb_detector/__init__.py`
- Create: `requirements/base.txt`
- Create: `requirements/windows.txt`
- Create: `requirements/macos.txt`

**Step 1: Create directories**

```bash
cd /Users/warezzko/Desktop/netfl/bb-detector
mkdir -p bb_detector assets/templates requirements build tests
```

**Step 2: Create __init__.py**

```python
# bb_detector/__init__.py
__version__ = "1.0.0"
```

**Step 3: Create base requirements**

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

**Step 4: Create Windows requirements**

```text
# requirements/windows.txt
-r base.txt
bettercam>=1.0.0
```

**Step 5: Create macOS requirements**

```text
# requirements/macos.txt
-r base.txt
pyobjc-core>=10.0
pyobjc-framework-Cocoa>=10.0
pyobjc-framework-Quartz>=10.0
```

**Step 6: Commit**

```bash
git add -A
git commit -m "feat: initial project structure and requirements"
```

---

### Task 2: Config Module

**Files:**
- Create: `bb_detector/config.py`
- Create: `tests/test_config.py`

**Step 1: Write the failing test**

```python
# tests/test_config.py
import pytest
import json
import tempfile
from pathlib import Path

def test_config_load_default():
    """Config returns defaults when file doesn't exist"""
    from bb_detector.config import Config

    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config(Path(tmpdir) / "config.json")

        assert config.get('detection.fps') == 10
        assert config.get('detection.death_threshold') == 0.75
        assert config.get('overlay.enabled') == True

def test_config_set_and_get():
    """Config can set and get nested values"""
    from bb_detector.config import Config

    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config(Path(tmpdir) / "config.json")

        config.set('profile.name', 'testuser')
        assert config.get('profile.name') == 'testuser'

def test_config_save_and_load():
    """Config persists to file"""
    from bb_detector.config import Config

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "config.json"

        config1 = Config(path)
        config1.set('profile.name', 'saved_user')
        config1.save()

        config2 = Config(path)
        config2.load()
        assert config2.get('profile.name') == 'saved_user'
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/warezzko/Desktop/netfl/bb-detector
python -m pytest tests/test_config.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'bb_detector.config'"

**Step 3: Write implementation**

```python
# bb_detector/config.py
import json
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = {
    "profile": {
        "name": None,
        "password": None,
        "auto_connect": True
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
            "custom": None
        }
    },
    "hotkeys": {
        "manual_death": "ctrl+shift+d",
        "toggle_boss": "ctrl+shift+b",
        "toggle_detection": "ctrl+shift+p",
        "show_overlay": "ctrl+shift+o"
    },
    "overlay": {
        "enabled": True,
        "position": [50, 50],
        "opacity": 0.85,
        "scale": 1.0
    },
    "calibration": {
        "completed": False,
        "death_region": None
    }
}


class Config:
    def __init__(self, path: Path | str | None = None):
        if path is None:
            path = Path.home() / ".bb-detector" / "config.json"
        self.path = Path(path)
        self._data = self._deep_copy(DEFAULT_CONFIG)

    def _deep_copy(self, obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(v) for v in obj]
        return obj

    def load(self) -> bool:
        if not self.path.exists():
            return False

        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            self._merge(self._data, loaded)
            return True
        except (json.JSONDecodeError, IOError):
            return False

    def _merge(self, base: dict, updates: dict):
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge(base[key], value)
            else:
                base[key] = value

    def save(self) -> bool:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self._data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value if value is not None else default

    def set(self, key: str, value: Any):
        keys = key.split('.')
        data = self._data

        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]

        data[keys[-1]] = value
```

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_config.py -v
```

Expected: PASS (3 passed)

**Step 5: Commit**

```bash
git add bb_detector/config.py tests/test_config.py
git commit -m "feat: add config module with load/save/get/set"
```

---

### Task 3: Platform Utils Module

**Files:**
- Create: `bb_detector/platform_utils.py`
- Create: `tests/test_platform_utils.py`

**Step 1: Write the failing test**

```python
# tests/test_platform_utils.py
import pytest
import platform

def test_get_platform():
    """get_platform returns current platform"""
    from bb_detector.platform_utils import get_platform

    result = get_platform()
    assert result in ['windows', 'macos', 'linux']

def test_get_scale_factor():
    """get_scale_factor returns a positive number"""
    from bb_detector.platform_utils import get_scale_factor

    result = get_scale_factor()
    assert isinstance(result, float)
    assert result >= 1.0
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_platform_utils.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write implementation**

```python
# bb_detector/platform_utils.py
import platform
import subprocess
from typing import Dict

def get_platform() -> str:
    system = platform.system()
    if system == 'Windows':
        return 'windows'
    elif system == 'Darwin':
        return 'macos'
    else:
        return 'linux'


def get_scale_factor() -> float:
    if get_platform() != 'macos':
        return 1.0

    try:
        from AppKit import NSScreen
        screen = NSScreen.mainScreen()
        return float(screen.backingScaleFactor())
    except ImportError:
        return 1.0
    except Exception:
        return 1.0


def check_macos_permissions() -> Dict[str, bool]:
    if get_platform() != 'macos':
        return {'screen': True, 'accessibility': True}

    result = {'screen': False, 'accessibility': False}

    # Check Screen Recording
    try:
        import mss
        sct = mss.mss()
        frame = sct.grab(sct.monitors[1])
        import numpy as np
        arr = np.array(frame)
        if arr.sum() > 0:
            result['screen'] = True
    except Exception:
        pass

    # Check Accessibility
    try:
        cmd = ['osascript', '-e', 'tell application "System Events" to return true']
        proc = subprocess.run(cmd, capture_output=True, timeout=2)
        result['accessibility'] = proc.returncode == 0
    except Exception:
        pass

    return result


def open_macos_permissions():
    if get_platform() != 'macos':
        return

    subprocess.run([
        'open',
        'x-apple.systempreferences:com.apple.preference.security?Privacy'
    ])
```

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_platform_utils.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add bb_detector/platform_utils.py tests/test_platform_utils.py
git commit -m "feat: add platform utils with macos permission checks"
```

---

## Phase 2: Screen Capture

### Task 4: Screen Capture Module

**Files:**
- Create: `bb_detector/capture.py`
- Create: `tests/test_capture.py`

**Step 1: Write the failing test**

```python
# tests/test_capture.py
import pytest
import numpy as np

def test_capture_grab_returns_numpy():
    """grab() returns a numpy array"""
    from bb_detector.capture import ScreenCapture

    capture = ScreenCapture(monitor=0)
    frame = capture.grab()

    assert isinstance(frame, np.ndarray)
    assert len(frame.shape) == 3  # Height, Width, Channels
    assert frame.shape[2] == 3    # RGB

def test_capture_resolution():
    """resolution property returns tuple"""
    from bb_detector.capture import ScreenCapture

    capture = ScreenCapture(monitor=0)
    res = capture.resolution

    assert isinstance(res, tuple)
    assert len(res) == 2
    assert res[0] > 0 and res[1] > 0
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_capture.py -v
```

Expected: FAIL

**Step 3: Write implementation**

```python
# bb_detector/capture.py
import numpy as np
from .platform_utils import get_platform

class ScreenCapture:
    def __init__(self, monitor: int = 0, fps: int = 10):
        self.monitor = monitor
        self.fps = fps
        self._platform = get_platform()
        self._backend = None
        self._camera = None
        self._sct = None
        self._monitor_info = None
        self._resolution = None

        self._init_backend()

    def _init_backend(self):
        # Try bettercam on Windows
        if self._platform == 'windows':
            try:
                import bettercam
                self._backend = 'bettercam'
                self._camera = bettercam.create(output_idx=self.monitor)
                return
            except (ImportError, Exception):
                pass

        # Fallback: mss (cross-platform)
        import mss
        self._backend = 'mss'
        self._sct = mss.mss()
        # mss monitors: 0 = all, 1+ = individual
        monitor_idx = min(self.monitor + 1, len(self._sct.monitors) - 1)
        self._monitor_info = self._sct.monitors[monitor_idx]
        self._resolution = (self._monitor_info['width'], self._monitor_info['height'])

    def start(self):
        if self._backend == 'bettercam' and self._camera:
            self._camera.start(target_fps=self.fps)

    def stop(self):
        if self._backend == 'bettercam' and self._camera:
            self._camera.stop()

    def grab(self) -> np.ndarray | None:
        if self._backend == 'bettercam':
            frame = self._camera.get_latest_frame()
            if frame is not None:
                self._resolution = (frame.shape[1], frame.shape[0])
            return frame

        elif self._backend == 'mss':
            screenshot = self._sct.grab(self._monitor_info)
            frame = np.array(screenshot)
            # Remove alpha channel and convert BGRA -> RGB
            frame = frame[:, :, :3]
            frame = frame[:, :, ::-1].copy()
            return frame

        return None

    def grab_region(self, x: int, y: int, w: int, h: int) -> np.ndarray | None:
        if self._backend == 'bettercam':
            frame = self.grab()
            if frame is not None:
                return frame[y:y+h, x:x+w]
            return None

        elif self._backend == 'mss':
            region = {
                'left': self._monitor_info['left'] + x,
                'top': self._monitor_info['top'] + y,
                'width': w,
                'height': h
            }
            screenshot = self._sct.grab(region)
            frame = np.array(screenshot)[:, :, :3][:, :, ::-1].copy()
            return frame

        return None

    @property
    def resolution(self) -> tuple[int, int]:
        if self._resolution:
            return self._resolution
        return (1920, 1080)

    @property
    def backend(self) -> str:
        return self._backend
```

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_capture.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add bb_detector/capture.py tests/test_capture.py
git commit -m "feat: add cross-platform screen capture module"
```

---

## Phase 3: Detection

### Task 5: Death Detector Module

**Files:**
- Create: `bb_detector/detector.py`
- Create: `tests/test_detector.py`
- Create: `assets/templates/you_died_en.png` (placeholder)

**Step 1: Write the failing test**

```python
# tests/test_detector.py
import pytest
import numpy as np
import cv2
from pathlib import Path

def test_detector_init():
    """Detector initializes with config"""
    from bb_detector.detector import DeathDetector
    from bb_detector.config import Config

    config = Config()
    detector = DeathDetector(config)

    assert detector.threshold == 0.75

def test_detector_check_death_no_match():
    """check_death returns False for blank frame"""
    from bb_detector.detector import DeathDetector
    from bb_detector.config import Config

    config = Config()
    detector = DeathDetector(config)

    # Create blank frame
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)

    is_dead, confidence = detector.check_death(frame)

    assert is_dead == False
    assert confidence < 0.5
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_detector.py -v
```

Expected: FAIL

**Step 3: Create placeholder template**

```python
# Run this once to create a placeholder template
import cv2
import numpy as np
from pathlib import Path

# Create a simple "YOU DIED" template (red text on dark background)
template = np.zeros((100, 400, 3), dtype=np.uint8)
template[:, :] = [20, 20, 20]  # Dark background

# Add red text placeholder
cv2.putText(template, "YOU DIED", (50, 70),
            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 200), 3)

path = Path("/Users/warezzko/Desktop/netfl/bb-detector/assets/templates")
path.mkdir(parents=True, exist_ok=True)
cv2.imwrite(str(path / "you_died_en.png"), template)
cv2.imwrite(str(path / "you_died_ru.png"), template)  # Same for now
```

**Step 4: Write implementation**

```python
# bb_detector/detector.py
import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Optional

from .config import Config


class DeathDetector:
    def __init__(self, config: Config):
        self.config = config
        self.threshold = config.get('detection.death_threshold', 0.75)
        self.template = None
        self.template_gray = None

        self._load_template()

    def _load_template(self):
        # Try custom template first
        custom = self.config.get('templates.death.custom')
        if custom:
            custom_path = Path(custom)
            if custom_path.exists():
                self.template = cv2.imread(str(custom_path))
                if self.template is not None:
                    self.template_gray = cv2.cvtColor(self.template, cv2.COLOR_BGR2GRAY)
                    return

        # Fall back to builtin
        builtin = self.config.get('templates.death.builtin', 'you_died_en.png')

        # Check multiple locations
        possible_paths = [
            Path(__file__).parent.parent / 'assets' / 'templates' / builtin,
            Path.cwd() / 'assets' / 'templates' / builtin,
            Path(__file__).parent / 'assets' / 'templates' / builtin,
        ]

        for template_path in possible_paths:
            if template_path.exists():
                self.template = cv2.imread(str(template_path))
                if self.template is not None:
                    self.template_gray = cv2.cvtColor(self.template, cv2.COLOR_BGR2GRAY)
                    return

        # Create minimal fallback template
        self.template = np.zeros((50, 200, 3), dtype=np.uint8)
        self.template_gray = np.zeros((50, 200), dtype=np.uint8)

    def reload(self, config: Config):
        self.config = config
        self.threshold = config.get('detection.death_threshold', 0.75)
        self._load_template()

    def check_death(self, frame: np.ndarray) -> Tuple[bool, float]:
        if frame is None or self.template_gray is None:
            return False, 0.0

        # Convert to grayscale
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        else:
            gray = frame

        # Resize template if needed (handle different resolutions)
        template = self.template_gray

        # Template matching
        try:
            result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            return max_val >= self.threshold, float(max_val)
        except cv2.error:
            return False, 0.0

    def check_death_region(self, frame: np.ndarray,
                           region: Optional[Tuple[int, int, int, int]] = None) -> Tuple[bool, float]:
        if region:
            x, y, w, h = region
            frame = frame[y:y+h, x:x+w]

        return self.check_death(frame)
```

**Step 5: Run test to verify it passes**

```bash
python -m pytest tests/test_detector.py -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add bb_detector/detector.py tests/test_detector.py assets/templates/
git commit -m "feat: add death detector with template matching"
```

---

## Phase 4: WebSocket Client

### Task 6: WebSocket Client Module

**Files:**
- Create: `bb_detector/websocket_client.py`
- Create: `tests/test_websocket_client.py`

**Step 1: Write the failing test**

```python
# tests/test_websocket_client.py
import pytest

def test_websocket_client_init():
    """WebSocket client initializes with profile"""
    from bb_detector.websocket_client import BBWebSocket

    ws = BBWebSocket(
        profile='testprofile',
        password='testpass',
        on_state=lambda s: None,
        on_connect=lambda: None,
        on_disconnect=lambda: None
    )

    assert ws.profile == 'testprofile'
    assert ws.authenticated == False
    assert 'testprofile' in ws.url

def test_websocket_message_builders():
    """Message builder methods return correct format"""
    from bb_detector.websocket_client import BBWebSocket

    ws = BBWebSocket('test', 'pass', lambda s: None, lambda: None, lambda: None)

    death_msg = ws._build_message('bb-death')
    assert death_msg == '{"type": "bb-death"}'

    victory_msg = ws._build_message('bb-boss-victory', name='Test Boss')
    assert '"type": "bb-boss-victory"' in victory_msg
    assert '"name": "Test Boss"' in victory_msg
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_websocket_client.py -v
```

Expected: FAIL

**Step 3: Write implementation**

```python
# bb_detector/websocket_client.py
import asyncio
import json
from typing import Callable, Optional, Dict, Any

import websockets
from websockets.exceptions import ConnectionClosed


class BBWebSocket:
    WS_URL = "wss://watch.home.kg/ws"

    def __init__(
        self,
        profile: str,
        password: str,
        on_state: Callable[[Dict], None],
        on_connect: Callable[[], None],
        on_disconnect: Callable[[], None]
    ):
        self.profile = profile
        self.password = password
        self.on_state = on_state
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect

        self.url = f"{self.WS_URL}?bloodborne=true&profile={profile}"
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.authenticated = False
        self._running = False
        self._reconnect_delay = 3.0

    def _build_message(self, msg_type: str, **kwargs) -> str:
        data = {'type': msg_type, **kwargs}
        return json.dumps(data)

    async def connect(self):
        self._running = True

        while self._running:
            try:
                async with websockets.connect(self.url) as ws:
                    self.ws = ws
                    await self._handle_connection()
            except ConnectionClosed:
                pass
            except Exception as e:
                print(f"[WS] Connection error: {e}")

            if self._running:
                self.authenticated = False
                self.on_disconnect()
                await asyncio.sleep(self._reconnect_delay)

    async def _handle_connection(self):
        self.on_connect()

        async for message in self.ws:
            try:
                data = json.loads(message)
                await self._handle_message(data)
            except json.JSONDecodeError:
                pass

    async def _handle_message(self, data: Dict):
        msg_type = data.get('type')

        if msg_type == 'bb-state':
            # Auto-auth if we have password and no edit rights
            if not data.get('canEdit') and self.password and not self.authenticated:
                await self._auth()

            if data.get('canEdit'):
                self.authenticated = True

            self.on_state(data)

        elif msg_type == 'bb-auth-result':
            self.authenticated = data.get('success', False)
            if self.authenticated:
                print("[WS] Authenticated successfully")
            else:
                print(f"[WS] Auth failed: {data.get('error')}")

    async def _auth(self):
        if self.ws:
            msg = self._build_message('bb-auth', password=self.password)
            await self.ws.send(msg)

    async def _send(self, msg_type: str, **kwargs):
        if self.ws and self.authenticated:
            msg = self._build_message(msg_type, **kwargs)
            await self.ws.send(msg)

    async def send_death(self):
        await self._send('bb-death')

    async def send_boss_death(self):
        await self._send('bb-boss-death')

    async def boss_start(self):
        await self._send('bb-boss-start')

    async def boss_pause(self):
        await self._send('bb-boss-pause')

    async def boss_resume(self):
        await self._send('bb-boss-resume')

    async def boss_victory(self, name: str):
        await self._send('bb-boss-victory', name=name)

    async def boss_cancel(self):
        await self._send('bb-boss-cancel')

    async def disconnect(self):
        self._running = False
        if self.ws:
            await self.ws.close()
            self.ws = None
```

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_websocket_client.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add bb_detector/websocket_client.py tests/test_websocket_client.py
git commit -m "feat: add websocket client with auto-reconnect"
```

---

## Phase 5: Global Hotkeys

### Task 7: Hotkeys Module

**Files:**
- Create: `bb_detector/hotkeys.py`
- Create: `tests/test_hotkeys.py`

**Step 1: Write the failing test**

```python
# tests/test_hotkeys.py
import pytest

def test_hotkeys_register():
    """Hotkeys can register callbacks"""
    from bb_detector.hotkeys import GlobalHotkeys

    hotkeys = GlobalHotkeys()
    callback_called = [False]

    def test_callback():
        callback_called[0] = True

    hotkeys.register('ctrl+shift+t', test_callback)

    assert frozenset(['ctrl', 'shift', 't']) in hotkeys.hotkeys

def test_hotkeys_normalize_macos():
    """cmd normalizes to ctrl"""
    from bb_detector.hotkeys import GlobalHotkeys

    hotkeys = GlobalHotkeys()
    hotkeys.register('cmd+shift+d', lambda: None)

    assert frozenset(['ctrl', 'shift', 'd']) in hotkeys.hotkeys
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_hotkeys.py -v
```

Expected: FAIL

**Step 3: Write implementation**

```python
# bb_detector/hotkeys.py
import threading
from typing import Callable, Dict, Set
from pynput import keyboard


class GlobalHotkeys:
    def __init__(self):
        self.hotkeys: Dict[frozenset, Callable] = {}
        self.current_keys: Set[str] = set()
        self.listener: keyboard.Listener | None = None
        self._lock = threading.Lock()

    def register(self, keys: str, callback: Callable):
        key_set = frozenset(
            k.strip().lower().replace('cmd', 'ctrl')
            for k in keys.split('+')
        )
        self.hotkeys[key_set] = callback

    def unregister(self, keys: str):
        key_set = frozenset(
            k.strip().lower().replace('cmd', 'ctrl')
            for k in keys.split('+')
        )
        self.hotkeys.pop(key_set, None)

    def start(self):
        if self.listener is not None:
            return

        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()

    def stop(self):
        if self.listener:
            self.listener.stop()
            self.listener = None

    def _normalize_key(self, key) -> str | None:
        special_map = {
            keyboard.Key.ctrl_l: 'ctrl',
            keyboard.Key.ctrl_r: 'ctrl',
            keyboard.Key.cmd: 'ctrl',
            keyboard.Key.cmd_l: 'ctrl',
            keyboard.Key.cmd_r: 'ctrl',
            keyboard.Key.shift_l: 'shift',
            keyboard.Key.shift_r: 'shift',
            keyboard.Key.alt_l: 'alt',
            keyboard.Key.alt_r: 'alt',
            keyboard.Key.alt_gr: 'alt',
            keyboard.Key.space: 'space',
            keyboard.Key.enter: 'enter',
            keyboard.Key.esc: 'esc',
            keyboard.Key.tab: 'tab',
            keyboard.Key.backspace: 'backspace',
        }

        if key in special_map:
            return special_map[key]

        if hasattr(key, 'char') and key.char:
            return key.char.lower()

        if hasattr(key, 'name') and key.name:
            return key.name.lower()

        return None

    def _on_press(self, key):
        key_name = self._normalize_key(key)
        if not key_name:
            return

        with self._lock:
            self.current_keys.add(key_name)
            frozen = frozenset(self.current_keys)

            if frozen in self.hotkeys:
                callback = self.hotkeys[frozen]
                threading.Thread(target=callback, daemon=True).start()

    def _on_release(self, key):
        key_name = self._normalize_key(key)
        if key_name:
            with self._lock:
                self.current_keys.discard(key_name)
```

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_hotkeys.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add bb_detector/hotkeys.py tests/test_hotkeys.py
git commit -m "feat: add global hotkeys with pynput"
```

---

## Phase 6: UI Components

### Task 8: System Tray Module

**Files:**
- Create: `bb_detector/tray.py`

**Step 1: Write implementation** (UI components are hard to unit test)

```python
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
```

**Step 2: Commit**

```bash
git add bb_detector/tray.py
git commit -m "feat: add system tray with pystray"
```

---

### Task 9: Overlay Module

**Files:**
- Create: `bb_detector/overlay.py`

**Step 1: Write implementation**

```python
# bb_detector/overlay.py
import time
from typing import Dict, Optional
import dearpygui.dearpygui as dpg

from .config import Config


class Overlay:
    def __init__(self, config: Config):
        self.config = config
        self.visible = True
        self._initialized = False
        self._flash_reset_time: Optional[float] = None

        # State
        self.deaths = 0
        self.boss_mode = False
        self.boss_paused = False
        self.boss_deaths = 0
        self.connected = False
        self.detection_enabled = True

    def init(self):
        if self._initialized:
            return

        dpg.create_context()

        pos = self.config.get('overlay.position', [50, 50])
        opacity = self.config.get('overlay.opacity', 0.85)

        dpg.create_viewport(
            title='BB Detector',
            width=180,
            height=120,
            x_pos=pos[0],
            y_pos=pos[1],
            decorated=False,
            always_on_top=True,
            resizable=False,
        )

        # Theme
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (11, 11, 12, int(255 * opacity)))
                dpg.add_theme_color(dpg.mvThemeCol_Text, (240, 236, 228))
                dpg.add_theme_color(dpg.mvThemeCol_Border, (60, 60, 60))

        # Main window
        with dpg.window(tag='main', no_title_bar=True, no_resize=True, no_move=False):
            # Status row
            with dpg.group(horizontal=True):
                dpg.add_text("*", tag='status_dot', color=(100, 100, 100))
                dpg.add_text("", tag='status_text', color=(150, 150, 150))

            dpg.add_separator()
            dpg.add_spacer(height=5)

            # Deaths count
            dpg.add_text("0", tag='deaths_count', color=(240, 236, 228))
            dpg.add_text("DEATHS", color=(100, 100, 100))

            dpg.add_spacer(height=5)

            # Boss section (hidden by default)
            with dpg.group(tag='boss_section', show=False):
                dpg.add_separator()
                with dpg.group(horizontal=True):
                    dpg.add_text("BOSS", color=(196, 48, 48))
                    dpg.add_text("0", tag='boss_deaths', color=(196, 48, 48))

            # Detection status
            dpg.add_spacer(height=5)
            dpg.add_text("detection: ON", tag='detection_status', color=(80, 80, 80))

        dpg.bind_theme(theme)
        dpg.setup_dearpygui()
        dpg.show_viewport()

        self._initialized = True

    def update(self, state: Dict):
        if not self._initialized:
            return

        self.deaths = state.get('deaths', 0)
        self.boss_mode = state.get('boss_mode', False)
        self.boss_paused = state.get('boss_paused', False)
        self.boss_deaths = state.get('boss_deaths', 0)
        self.connected = state.get('connected', False)
        self.detection_enabled = state.get('detection_enabled', True)

        # Update UI
        dpg.set_value('deaths_count', str(self.deaths))
        dpg.set_value('boss_deaths', str(self.boss_deaths))

        # Connection status
        if self.connected:
            dpg.configure_item('status_dot', color=(0, 200, 0))
            dpg.set_value('status_text', '')
        else:
            dpg.configure_item('status_dot', color=(200, 0, 0))
            dpg.set_value('status_text', 'OFFLINE')

        # Boss section
        dpg.configure_item('boss_section', show=self.boss_mode)

        # Detection status
        status = 'detection: ON' if self.detection_enabled else 'detection: OFF'
        dpg.set_value('detection_status', status)

    def flash_death(self):
        if self._initialized:
            dpg.configure_item('deaths_count', color=(255, 50, 50))
            self._flash_reset_time = time.time() + 0.3

    def render(self):
        if not self._initialized:
            return

        # Reset flash
        if self._flash_reset_time and time.time() > self._flash_reset_time:
            dpg.configure_item('deaths_count', color=(240, 236, 228))
            self._flash_reset_time = None

        dpg.render_dearpygui_frame()

    def toggle_visibility(self):
        self.visible = not self.visible
        if self._initialized:
            if self.visible:
                dpg.show_viewport()
            else:
                dpg.minimize_viewport()

    def save_position(self):
        if self._initialized:
            pos = dpg.get_viewport_pos()
            self.config.set('overlay.position', list(pos))

    def destroy(self):
        if self._initialized:
            self.save_position()
            dpg.destroy_context()
            self._initialized = False

    def is_running(self) -> bool:
        if not self._initialized:
            return False
        return dpg.is_dearpygui_running()
```

**Step 2: Commit**

```bash
git add bb_detector/overlay.py
git commit -m "feat: add overlay window with dearpygui"
```

---

## Phase 7: Main Application

### Task 10: Main Module

**Files:**
- Create: `bb_detector/main.py`

**Step 1: Write implementation**

```python
# bb_detector/main.py
import asyncio
import platform
import signal
import time
from pathlib import Path

from .config import Config
from .platform_utils import get_platform, check_macos_permissions, open_macos_permissions
from .capture import ScreenCapture
from .detector import DeathDetector
from .websocket_client import BBWebSocket
from .overlay import Overlay
from .tray import TrayIcon
from .hotkeys import GlobalHotkeys


class BBDetectorApp:
    def __init__(self):
        self.config = Config()
        self.running = False

        # Components
        self.capture: ScreenCapture | None = None
        self.detector: DeathDetector | None = None
        self.ws: BBWebSocket | None = None
        self.overlay: Overlay | None = None
        self.tray: TrayIcon | None = None
        self.hotkeys: GlobalHotkeys | None = None

        # State
        self.detection_enabled = True
        self.boss_mode = False
        self.connected = False
        self.deaths = 0
        self.boss_deaths = 0
        self.last_death_time = 0

        # Async
        self.loop: asyncio.AbstractEventLoop | None = None

    def run(self):
        print("BB Death Detector starting...")

        # Check macOS permissions
        if get_platform() == 'macos':
            perms = check_macos_permissions()
            if not perms['screen'] or not perms['accessibility']:
                print("macOS permissions required!")
                print("Please enable Screen Recording and Accessibility")
                open_macos_permissions()
                return

        # Load config
        self.config.load()

        # Get profile from config or prompt
        profile = self.config.get('profile.name')
        password = self.config.get('profile.password')

        if not profile:
            profile = input("Enter profile name: ").strip()
            password = input("Enter password: ").strip()
            self.config.set('profile.name', profile)
            self.config.set('profile.password', password)
            self.config.save()

        # Initialize components
        self._init_components(profile, password)

        # Start
        self.running = True
        self._start()

    def _init_components(self, profile: str, password: str):
        monitor = self.config.get('detection.monitor', 0)
        fps = self.config.get('detection.fps', 10)

        self.capture = ScreenCapture(monitor=monitor, fps=fps)
        self.detector = DeathDetector(self.config)

        self.ws = BBWebSocket(
            profile=profile,
            password=password,
            on_state=self._on_ws_state,
            on_connect=self._on_ws_connect,
            on_disconnect=self._on_ws_disconnect
        )

        self.overlay = Overlay(self.config)

        self.tray = TrayIcon(
            on_quit=self._on_quit,
            on_settings=lambda: None,  # TODO
            on_toggle_overlay=self._on_toggle_overlay,
            on_toggle_detection=self._on_toggle_detection
        )

        self.hotkeys = GlobalHotkeys()
        self._register_hotkeys()

    def _register_hotkeys(self):
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
            self._on_toggle_overlay
        )

    def _start(self):
        # Setup signal handlers
        signal.signal(signal.SIGINT, lambda s, f: self._on_quit())
        signal.signal(signal.SIGTERM, lambda s, f: self._on_quit())

        # Start tray
        self.tray.start()

        # Start hotkeys
        self.hotkeys.start()

        # Start capture
        self.capture.start()

        # Initialize overlay
        self.overlay.init()

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
        # Start WebSocket connection
        ws_task = asyncio.create_task(self.ws.connect())

        fps = self.config.get('detection.fps', 10)
        interval = 1.0 / fps
        cooldown = self.config.get('detection.death_cooldown', 5.0)

        while self.running and self.overlay.is_running():
            loop_start = time.time()

            # Detection
            if self.detection_enabled and self.connected:
                frame = self.capture.grab()

                if frame is not None:
                    is_dead, confidence = self.detector.check_death(frame)

                    if is_dead:
                        now = time.time()
                        if now - self.last_death_time > cooldown:
                            self.last_death_time = now
                            await self._handle_death()

            # Update overlay
            self.overlay.update({
                'deaths': self.deaths,
                'boss_mode': self.boss_mode,
                'boss_deaths': self.boss_deaths,
                'connected': self.connected,
                'detection_enabled': self.detection_enabled
            })
            self.overlay.render()

            # FPS limiting
            elapsed = time.time() - loop_start
            await asyncio.sleep(max(0, interval - elapsed))

        ws_task.cancel()

    async def _handle_death(self):
        print("[Detector] Death detected!")

        if self.boss_mode:
            await self.ws.send_boss_death()
        else:
            await self.ws.send_death()

        self.overlay.flash_death()
        self.tray.notify("Death!", "BB")

    # === WebSocket callbacks ===

    def _on_ws_state(self, state: dict):
        self.deaths = state.get('deaths', 0)
        self.boss_mode = state.get('bossFightMode', False)
        self.boss_deaths = state.get('bossDeaths', 0)

    def _on_ws_connect(self):
        self.connected = True
        self.tray.set_connected(True)
        print("[WS] Connected")

    def _on_ws_disconnect(self):
        self.connected = False
        self.tray.set_connected(False)
        print("[WS] Disconnected")

    # === Hotkey callbacks ===

    def _on_manual_death(self):
        if not self.connected or not self.loop:
            return

        asyncio.run_coroutine_threadsafe(
            self.ws.send_boss_death() if self.boss_mode else self.ws.send_death(),
            self.loop
        )
        self.overlay.flash_death()

    def _on_toggle_boss(self):
        if not self.connected or not self.loop:
            return

        if self.boss_mode:
            asyncio.run_coroutine_threadsafe(self.ws.boss_cancel(), self.loop)
        else:
            asyncio.run_coroutine_threadsafe(self.ws.boss_start(), self.loop)

    def _on_toggle_detection(self):
        self.detection_enabled = not self.detection_enabled
        status = "ON" if self.detection_enabled else "OFF"
        self.tray.notify(f"Detection {status}", "BB")
        print(f"[App] Detection: {status}")

    def _on_toggle_overlay(self):
        self.overlay.toggle_visibility()

    def _on_quit(self):
        print("[App] Quit")
        self.running = False

    def _shutdown(self):
        print("[App] Shutting down...")

        self.hotkeys.stop()
        self.capture.stop()

        if self.loop and self.ws:
            self.loop.run_until_complete(self.ws.disconnect())

        self.overlay.destroy()
        self.tray.stop()
        self.config.save()

        print("[App] Goodbye!")


def main():
    app = BBDetectorApp()
    app.run()


if __name__ == '__main__':
    main()
```

**Step 2: Commit**

```bash
git add bb_detector/main.py
git commit -m "feat: add main application with full integration"
```

---

### Task 11: Entry Point

**Files:**
- Create: `bb_detector/__main__.py`

**Step 1: Write implementation**

```python
# bb_detector/__main__.py
from .main import main

if __name__ == '__main__':
    main()
```

**Step 2: Commit**

```bash
git add bb_detector/__main__.py
git commit -m "feat: add __main__.py entry point"
```

---

## Phase 8: Build Scripts

### Task 12: Build Configuration

**Files:**
- Create: `build/build_windows.py`
- Create: `build/build_macos.py`
- Create: `build.py`
- Create: `Makefile`

**Step 1: Create Windows build script**

```python
# build/build_windows.py
import PyInstaller.__main__
import shutil
import os

def build():
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            shutil.rmtree(folder)

    PyInstaller.__main__.run([
        'bb_detector/main.py',
        '--name=BBDetector',
        '--onefile',
        '--windowed',
        '--add-data=assets;assets',
        '--hidden-import=pynput.keyboard._win32',
        '--hidden-import=pynput.mouse._win32',
        '--exclude-module=matplotlib',
        '--exclude-module=scipy',
        '--exclude-module=pandas',
    ])

    print("Build complete: dist/BBDetector.exe")

if __name__ == '__main__':
    build()
```

**Step 2: Create macOS build script**

```python
# build/build_macos.py
from setuptools import setup
import shutil
import os

def build():
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            shutil.rmtree(folder)

    APP = ['bb_detector/main.py']
    DATA_FILES = [('assets', ['assets/templates/you_died_en.png'])]
    OPTIONS = {
        'argv_emulation': False,
        'bundle_identifier': 'kg.home.watch.bbdetector',
        'plist': {
            'CFBundleName': 'BB Death Detector',
            'CFBundleVersion': '1.0.0',
            'LSUIElement': True,
            'NSScreenCaptureUsageDescription': 'Screen capture for death detection',
        },
        'packages': ['dearpygui', 'cv2', 'mss', 'pynput', 'pystray', 'websockets'],
    }

    setup(
        name='BB Death Detector',
        app=APP,
        data_files=DATA_FILES,
        options={'py2app': OPTIONS},
        setup_requires=['py2app'],
    )

if __name__ == '__main__':
    build()
```

**Step 3: Create main build script**

```python
# build.py
import platform
import subprocess
import sys

def main():
    system = platform.system()
    print(f"Building for {system}...")

    if system == 'Windows':
        subprocess.run([sys.executable, 'build/build_windows.py'])
    elif system == 'Darwin':
        subprocess.run([sys.executable, 'build/build_macos.py', 'py2app'])
    else:
        print(f"Unsupported: {system}")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

**Step 4: Create Makefile**

```makefile
# Makefile
.PHONY: install dev build clean test

install:
	pip install -r requirements/base.txt

dev:
	python -m bb_detector

build:
	python build.py

clean:
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +

test:
	python -m pytest tests/ -v
```

**Step 5: Commit**

```bash
git add build/ build.py Makefile
git commit -m "feat: add build scripts for Windows and macOS"
```

---

## Final: Run Tests and Verify

### Task 13: Final Verification

**Step 1: Install dependencies**

```bash
cd /Users/warezzko/Desktop/netfl/bb-detector
pip install -r requirements/base.txt
```

**Step 2: Run all tests**

```bash
python -m pytest tests/ -v
```

Expected: All tests pass

**Step 3: Run the application**

```bash
python -m bb_detector
```

Expected: Application starts, shows overlay, connects to WebSocket

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat: BB Death Detector v1.0.0 complete"
```

---

## Summary

| Phase | Tasks | Status |
|-------|-------|--------|
| 1. Setup | Project structure, config, platform utils | [ ] |
| 2. Capture | Screen capture module | [ ] |
| 3. Detection | Death detector | [ ] |
| 4. Network | WebSocket client | [ ] |
| 5. Hotkeys | Global hotkeys | [ ] |
| 6. UI | Tray, Overlay | [ ] |
| 7. Integration | Main app | [ ] |
| 8. Build | Build scripts | [ ] |

Total: 13 tasks, ~20 steps
