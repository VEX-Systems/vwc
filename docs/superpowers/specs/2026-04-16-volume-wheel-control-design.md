# Volume Wheel Control - Design Specification

**Date:** 2026-04-16
**Status:** Draft
**Target hardware:** Ajazz AK820 (and any keyboard exposing standard HID consumer-control volume keys)
**Target OS:** Windows 10/11

## 1. Overview

Volume Wheel Control is a Windows tray application that turns the volume knob on a keyboard (or any source of `Volume Up`, `Volume Down`, `Volume Mute` events) into a fully programmable input device. Users assign macros to gestures: single click, double click, triple click, long press, rotate clockwise, rotate counter-clockwise. Macros can be different per active application via overrides.

The application is written in Python with a PyQt6 + qfluentwidgets GUI in English. It runs in the background with a system tray icon and minimal idle resource usage.

### 1.1 Primary use case

A user clicks the volume knob twice to skip the current track. The application detects the double click, suppresses the default mute action that Windows would otherwise perform, and sends a `Next Track` media key instead. A single click still triggers mute, with a small delay (~250 ms) to allow the detector to wait for a possible second click.

### 1.2 Goals

- Configurable macros for 6 gestures on the volume knob
- Per-application overrides on top of a global profile
- Native Windows 11 look (Fluent UI / Mica)
- No admin rights required for normal operation
- Single-file `.exe` build via PyInstaller
- Distinct, hand-crafted UI - must not look generic / AI-generated

### 1.3 Non-goals (initial release)

- Cross-platform support (Windows only)
- Per-device routing (we react to the OS-level keys, not to a specific HID device)
- Cloud sync of profiles
- Plugin / scripting system beyond the built-in action types
- Macro recording

## 2. Architecture

High-level component diagram:

```
+---------------------------------------------------------+
|                    Tray Icon (always on)                |
|  +------------+                  +------------------+   |
|  | Settings   | <- user opens -> |   Main Window    |   |
|  | Window     |                  |   (Fluent UI)    |   |
|  +------------+                  +------------------+   |
+---------------------------------------------------------+
                            |
                            v
+---------------------------------------------------------+
|                      Event Bus (Qt signals)             |
+---------------------------------------------------------+
     ^              ^                  ^              |
     |              |                  |              v
+---------+   +----------+      +----------+    +----------+
| Keyboard|   | Gesture  |      | Profile  |    |  Action  |
|  Hook   |-->| Detector |----->| Resolver |--->| Executor |
+---------+   +----------+      +----------+    +----------+
                                       |
                                       v
                                +----------+
                                | Active   |
                                | Window   |
                                | Watcher  |
                                +----------+

Storage: %APPDATA%/VolumeWheelControl/config.json
```

### 2.1 Event flow

1. **Keyboard Hook** captures multimedia keys (Volume Up / Down / Mute), optionally suppressing the default OS reaction so we control timing.
2. **Gesture Detector** is a state machine that aggregates raw key events into gestures: `single_click`, `double_click`, `triple_click`, `long_press`, `rotate_up`, `rotate_down`.
3. **Active Window Watcher** keeps a cache of the foreground window's process name and title, updated via `SetWinEventHook(EVENT_SYSTEM_FOREGROUND)`.
4. **Profile Resolver** looks up the binding for the detected gesture: it scans app overrides (first match wins), falls back to the global profile if no override binds that gesture.
5. **Action Executor** runs the bound action on a worker thread so slow actions (process spawn) do not block the event loop.

### 2.2 Lifecycle

- App starts headless with a tray icon. The main GUI is created lazily on first open.
- Closing the main window hides it; the process keeps running.
- Tray menu has explicit `Quit`.
- Hot reload: when the user saves config from GUI, the running components reload bindings without restarting the process or the hook.

### 2.3 Threading model

- Qt main thread: GUI, event bus, gesture detector, profile resolver, foreground watcher (its callback marshals to main thread).
- Hook thread (owned by the `keyboard` library): produces raw events, marshals them to main thread via `Qt.QueuedConnection`.
- Worker thread pool (`QThreadPool`): action execution.

## 3. Data model

### 3.1 Configuration file

Location: `%APPDATA%\VolumeWheelControl\config.json`. Atomic writes (write to `.tmp` then rename).

```json
{
  "version": 1,
  "settings": {
    "double_click_timeout_ms": 250,
    "long_press_threshold_ms": 500,
    "start_with_windows": true,
    "suppress_default_actions": true,
    "paused": false
  },
  "global_profile": {
    "single_click":  { "type": "media", "key": "mute" },
    "double_click":  { "type": "media", "key": "next_track" },
    "triple_click":  { "type": "media", "key": "previous_track" },
    "long_press":    { "type": "media", "key": "play_pause" },
    "rotate_up":     { "type": "media", "key": "volume_up" },
    "rotate_down":   { "type": "media", "key": "volume_down" }
  },
  "app_overrides": [
    {
      "name": "Spotify",
      "match": { "type": "process", "value": "Spotify.exe" },
      "bindings": {
        "double_click": { "type": "hotkey", "keys": "ctrl+right" }
      }
    },
    {
      "name": "VS Code",
      "match": { "type": "process", "value": "Code.exe" },
      "bindings": {
        "long_press": { "type": "hotkey", "keys": "ctrl+shift+p" }
      }
    }
  ]
}
```

### 3.2 Gestures

Fixed enum, six values:

- `single_click`
- `double_click`
- `triple_click`
- `long_press`
- `rotate_up` (clockwise)
- `rotate_down` (counter-clockwise)

### 3.3 Action types

All actions are JSON objects with a `type` discriminator.

| Type | Required fields | Optional fields | Notes |
|---|---|---|---|
| `media` | `key` ∈ {`play_pause`, `next_track`, `previous_track`, `stop`, `mute`, `volume_up`, `volume_down`} | - | Sends a multimedia key |
| `hotkey` | `keys` (string, `+`-separated) | - | e.g. `ctrl+shift+esc` |
| `run` | `path` (string) | `args` (string), `cwd` (string) | Launches a process detached from the app |
| `window` | `action` ∈ {`minimize`, `maximize`, `restore`, `close`, `minimize_all`, `switch_next`, `switch_prev`, `fullscreen`} | - | See window action semantics below |
| `none` | - | - | Explicitly disable a gesture (suppress without doing anything) |

#### 3.3.1 Window action semantics

| Action | Target | Implementation |
|---|---|---|
| `minimize` | foreground window | `ShowWindow(hwnd, SW_MINIMIZE)` |
| `maximize` | foreground window | `ShowWindow(hwnd, SW_MAXIMIZE)` |
| `restore` | foreground window | `ShowWindow(hwnd, SW_RESTORE)` |
| `close` | foreground window | `PostMessage(hwnd, WM_CLOSE, 0, 0)` |
| `minimize_all` | all windows | `keyboard.send("win+d")` |
| `switch_next` | OS switcher | `keyboard.send("alt+tab")` |
| `switch_prev` | OS switcher | `keyboard.send("alt+shift+tab")` |
| `fullscreen` | foreground window | `keyboard.send("f11")` (works for browsers and most media apps; not a true OS-level fullscreen toggle) |

If no foreground window is available (locked screen, transient state), foreground-targeted actions log a warning and do nothing.

### 3.4 Match strategies (for app overrides)

| Type | Field | Behaviour |
|---|---|---|
| `process` | `value` | Case-insensitive exact match against the foreground process exe name |
| `title_contains` | `value` | Case-insensitive substring match against the foreground window title |
| `title_regex` | `value` | Python `re.search` against the title; invalid regex disables the rule with a warning logged |

### 3.5 Resolver semantics

For a given gesture and current foreground context:

1. Iterate `app_overrides` in declared order.
2. For each, evaluate its match strategy against the cached foreground process / title.
3. The **first matching override** is selected.
4. If that override defines a binding for the gesture, return it.
5. Otherwise, return the binding from `global_profile` for the gesture (per-gesture fallback within a matched profile, not per-profile fallback).
6. If no override matches at all, return `global_profile[gesture]`.

`global_profile` must define every gesture. Schema validation enforces this.

## 4. Gesture detection

### 4.1 Click state machine (for the Mute key)

States: `IDLE`, `PRESSED`, `WAIT_FOR_NEXT`, `LONG_HOLDING`, `PRESSED_AGAIN`.
Inputs: `DOWN`, `UP`, `TIMEOUT_DBL`, `TIMEOUT_LONG`.

```
IDLE --DOWN--> PRESSED
              start TIMEOUT_LONG (long_press_threshold_ms)
              click_count = 1

PRESSED --UP--> WAIT_FOR_NEXT
              cancel TIMEOUT_LONG
              start TIMEOUT_DBL (double_click_timeout_ms)

PRESSED --TIMEOUT_LONG--> LONG_HOLDING
              emit gesture: long_press
              click_count = 0

LONG_HOLDING --UP--> IDLE

WAIT_FOR_NEXT --DOWN--> PRESSED_AGAIN
              cancel TIMEOUT_DBL
              click_count++

PRESSED_AGAIN --UP--> WAIT_FOR_NEXT
              start TIMEOUT_DBL again

WAIT_FOR_NEXT --TIMEOUT_DBL--> IDLE
              emit gesture based on click_count:
                1 -> single_click
                2 -> double_click
                3 -> triple_click
                4+ -> triple_click  (cap, no error)
              click_count = 0
```

Notes:
- `TIMEOUT_LONG` only runs while the key is held (state `PRESSED`). It is cancelled on release.
- After `long_press` is emitted, further presses on the same physical down event do nothing; the next cycle starts on the next `DOWN`.
- Repeat events from the OS while the key is held (key-repeat) must be filtered: only the first `DOWN` per physical press counts. Detected by tracking `is_down`; subsequent `DOWN` while `is_down=True` is ignored until an `UP` is seen.

### 4.2 Rotation handling

Volume Up / Volume Down events do not need a state machine. Each `DOWN` event emits one `rotate_up` or `rotate_down` gesture immediately.

### 4.3 Suppression strategy

- When `settings.suppress_default_actions` is `true`, the hook suppresses the Mute key unconditionally. The detector decides what to send. The cost is a `double_click_timeout_ms` delay on `single_click → mute`.
- For Volume Up / Down, suppression is conditional: if the bound action for the gesture is `media: volume_up` / `media: volume_down`, the hook does **not** suppress (pass-through, no delay). Otherwise it suppresses and the executor runs the bound action.
- When `suppress_default_actions` is `false`, the hook never suppresses. The Mute key always mutes immediately; `double_click`, `triple_click`, `long_press` cease to function. The Settings page displays this trade-off in plain text next to the toggle.

## 5. GUI design

### 5.1 Main window

`FluentWindow` with a left `NavigationInterface`. Pages:

1. **Bindings** - global profile editing.
2. **Profiles** - app overrides as cards with edit / delete.
3. **Settings** - timeouts, autostart, suppression, pause, open config folder.
4. **About** - version, repo link, license.

Theme: Fluent UI dark by default, follows system theme. Mica acrylic background on the main window where supported.

### 5.2 Bindings page layout

Two regions stacked vertically:

```
+--------------------------------------------------------------+
| Global Bindings                                              |
| ----------------------------------------                     |
|                                                              |
| Single click       [v Mute              ]  selected          |
| Double click       [v Next track        ]                    |
| Triple click       [v Previous track    ]                    |
| Long press         [v Play / Pause      ]                    |
| Rotate clockwise   [v Volume up         ]                    |
| Rotate counter-cw  [v Volume down       ]                    |
+--------------------------------------------------------------+
| Action: <type-specific editor>                               |
|                                                              |
| <fields specific to action type>                             |
|                                                              |
|                                  [Test]    [Save]            |
+--------------------------------------------------------------+
```

Each gesture row has a combo box with the action type as a summary label ("Mute", "Hotkey: Ctrl+Right", "Run: spotify.exe"). Selecting a row populates the editor below. `Test` constructs an action from the editor's current values and runs `execute()` once without saving config. `Save` writes config and triggers hot reload through the `configChanged` signal on the bus; the resolver and dispatcher pick up the new config on the next gesture without restarting the hook.

### 5.3 Action editors

Dispatched by action type:

- `media` - combo box with the 7 media keys.
- `hotkey` - a custom `KeySequenceEdit` widget: focus and press the desired combo to capture, with a clear button. Stored as `+`-separated string.
- `run` - text field for path with a Browse button (`QFileDialog`), text field for arguments, optional working directory.
- `window` - combo box with the 8 window actions.
- `none` - placeholder text "This gesture is disabled".

### 5.4 Profiles page

List of `CardWidget` items:

```
+---------------------------------------------+
|  [icon] Spotify                             |
|  Match: process = Spotify.exe               |
|  3 custom bindings              [Edit] [x]  |
+---------------------------------------------+
[+ Add app override]
```

`Edit` opens an `OverrideDialog` with:
- Name (free text)
- Match type (combo: process / title_contains / title_regex)
- Match value (text input; regex variant validates on the fly)
- Bindings section: same six gesture rows as the global page, plus a "Use global" toggle per row to delete the override for that gesture.

### 5.5 Settings page

`SettingsCard`-style entries:

- Double-click timeout (slider 100-500 ms, label shows current value)
- Long-press threshold (slider 300-1000 ms)
- Suppress default actions (toggle, with explanatory text about the mute delay trade-off)
- Start with Windows (toggle, writes to `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`)
- Pause detection (toggle, mirrored in tray menu)
- Open config folder (button)

### 5.6 Tray icon

Two icon variants: `tray-active.png` and `tray-paused.png`. Right-click menu:

```
* Volume Wheel Control
-----------------
  Open
  Pause detection      [v]
-----------------
  Reload config
  Open config folder
-----------------
  Quit
```

Left-click opens the main window.

### 5.7 Visual identity guidance

The app must not look like a stock template:

- Custom app icon (designed asset, not a generic symbol)
- Restrained typography: Segoe UI Variable for body, weight contrast in headings only, no decorative fonts
- Mica background on the main window where the OS supports it; solid Fluent dark fallback otherwise
- Accent color follows the system accent
- No emoji, no generic gradient cards, no centered hero sections, no "modern app" placeholder text
- Page-specific empty states with concrete, useful copy ("No app overrides yet. Click Add to bind different actions for a specific app.")

## 6. Module structure

```
VolumeWheelControl/
|-- pyproject.toml
|-- README.md
|-- LICENSE
|-- docs/
|   `-- superpowers/specs/2026-04-16-volume-wheel-control-design.md
|-- resources/
|   |-- icons/{app.ico,tray-active.png,tray-paused.png}
|   `-- qss/overrides.qss
|-- src/volume_wheel_control/
|   |-- __init__.py
|   |-- __main__.py
|   |-- app.py                     # orchestration: wires hook, detector, resolver, executor, GUI
|   |-- bus.py                     # EventBus QObject with signals
|   |-- input/
|   |   |-- keyboard_hook.py
|   |   `-- raw_events.py
|   |-- gestures/
|   |   |-- detector.py
|   |   |-- gestures.py
|   |   `-- timer.py
|   |-- windows/
|   |   |-- foreground_watcher.py
|   |   |-- window_actions.py
|   |   `-- autostart.py
|   |-- profiles/
|   |   |-- resolver.py
|   |   `-- matchers.py
|   |-- actions/
|   |   |-- base.py
|   |   |-- registry.py
|   |   |-- media.py
|   |   |-- hotkey.py
|   |   |-- run.py
|   |   |-- window.py
|   |   `-- noop.py
|   |-- config/
|   |   |-- models.py
|   |   |-- storage.py
|   |   |-- paths.py
|   |   |-- defaults.py
|   |   `-- migrations.py
|   `-- ui/
|       |-- theme.py
|       |-- tray.py
|       |-- main_window.py
|       |-- pages/{bindings,profiles,settings,about}_page.py
|       |-- editors/{action,media,hotkey,run,window}_editor.py
|       `-- dialogs/override_dialog.py
`-- tests/
    |-- conftest.py
    |-- test_gesture_detector.py
    |-- test_profile_resolver.py
    |-- test_action_registry.py
    |-- test_config_storage.py
    `-- test_matchers.py
```

### 6.1 Module responsibilities

| Module | Responsibility | Depends on |
|---|---|---|
| `app.py` | Construct components, wire signals, run Qt event loop | All |
| `bus.py` | Define `EventBus` with named signals (`rawEvent`, `gestureDetected`, `configChanged`, `pauseToggled`) | PyQt6 |
| `input/keyboard_hook.py` | Install / remove low-level hook, emit raw events, configure suppression | `keyboard`, bus |
| `gestures/detector.py` | State machine, timers, emit gestures | `QTimer`, bus |
| `windows/foreground_watcher.py` | Track foreground process and title | `pywin32`, `psutil`, bus |
| `windows/window_actions.py` | Pure helpers for window operations | `pywin32` |
| `windows/autostart.py` | Read / write the Run registry key | `pywin32` |
| `profiles/resolver.py` | Pure function: gesture + context + config -> action dict | `profiles/matchers.py` |
| `profiles/matchers.py` | Pure predicates per match strategy | stdlib |
| `actions/*` | One class per action type, each with `execute()` | `keyboard`, `subprocess`, `pywin32` |
| `actions/registry.py` | Build action instance from JSON dict; central type registration | `actions/*` |
| `config/models.py` | Pydantic dataclasses with validation | `pydantic` |
| `config/storage.py` | Atomic load / save | `config/models.py` |
| `config/migrations.py` | Forward migrations between schema versions | `config/models.py` |
| `ui/*` | All Qt widgets, no business logic; talks to bus and config storage | `PyQt6`, `qfluentwidgets` |

## 7. Dependencies

Runtime:

| Package | Purpose |
|---|---|
| `PyQt6` | GUI |
| `PyQt6-Fluent-Widgets` | Fluent UI components |
| `keyboard` | Low-level keyboard hook with suppression |
| `pywin32` | win32gui, win32process, registry, SetWinEventHook |
| `psutil` | Process name from PID |
| `pydantic` | Config validation |

Development:

| Package | Purpose |
|---|---|
| `pytest` | Test runner |
| `pytest-qt` | Qt signal / widget testing |
| `pytest-mock` | Mocking helper |
| `ruff` | Lint + format |
| `mypy` | Type checking |
| `pyinstaller` | Build standalone .exe |

## 8. Testing strategy

Automated unit tests, no Windows API in CI:

- `test_gesture_detector.py` - feed raw events, advance fake timers, assert emitted gestures cover all paths in the state machine including key repeat, all click counts, long press cancellation by release, pure rotation events.
- `test_profile_resolver.py` - assert override precedence, per-gesture fallback inside a matched profile, fallback to global profile when no override matches.
- `test_matchers.py` - case sensitivity, regex validity, missing process / title.
- `test_action_registry.py` - roundtrip: dict -> action -> dict; unknown type raises clear error.
- `test_config_storage.py` - load / save in tmpdir, atomic write semantics (corrupt partial file does not replace good config), defaults applied for missing optional fields.

Mocked tests for actions: `MediaAction`, `HotkeyAction`, `RunAction`, `WindowAction` against mocked `keyboard.send`, `subprocess.Popen`, `win32gui` calls.

Manual smoke tests (documented in `README.md`):

1. Run on Windows 11, hook installs without admin
2. Volume knob mute is delayed by ~250 ms but works
3. Double click triggers `Next Track`
4. Triple click triggers `Previous Track`
5. Long press triggers `Play / Pause`
6. Rotation up / down adjusts system volume immediately
7. Spotify override: double click sends `Ctrl+Right` only when Spotify is in foreground
8. Tray menu Pause stops detection; Resume restores it
9. Autostart toggle creates / removes registry key and survives reboot
10. PyInstaller build runs on a clean Windows machine without Python installed

## 9. Build and distribution

PyInstaller command (driven by a `build.py` helper or documented in README):

```
pyinstaller \
  --noconfirm \
  --noconsole \
  --onefile \
  --name VolumeWheelControl \
  --icon resources/icons/app.ico \
  --add-data "resources;resources" \
  src/volume_wheel_control/__main__.py
```

Output: `dist/VolumeWheelControl.exe` (~30-40 MB).

## 10. Operational notes

- No admin rights required for normal use.
- The `keyboard` library may behave unpredictably if another process also installs a global hook; this is documented in the README troubleshooting section.
- Crash recovery: `app.py` wraps the executor in a try/except per action; an exception in one action logs and continues, never tears down the hook.
- Logs: rotating file at `%APPDATA%\VolumeWheelControl\logs\app.log`, INFO by default, DEBUG togglable from Settings.

## 11. Constraints from the user

- Code is written in English (identifiers, UI strings, log messages).
- Source code contains no comments. Code must be self-explanatory through naming and structure.
- The application's visual design must be deliberate and not resemble generic AI-generated UI: custom icon, restrained typography, native Windows look, no emoji, page-specific empty-state copy.
