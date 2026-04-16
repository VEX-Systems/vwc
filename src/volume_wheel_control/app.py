from __future__ import annotations

import logging
import logging.handlers
import os
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from .actions.registry import build_action
from .bus import EventBus
from .config import paths
from .config.models import ActionConfig, AppOverride, Config, Settings
from .config.storage import ConfigStorage
from .gestures.detector import GestureDetector
from .gestures.gestures import Gesture
from .gestures.qt_timer import QtTimerFactory
from .input.keyboard_hook import KeyboardHook
from .profiles.matchers import WindowContext
from .profiles.resolver import resolve
from .ui import theme
from .ui.main_window import MainWindow
from .ui.tray import TrayController
from .windows import autostart
from .windows.foreground_watcher import ForegroundWatcher


log = logging.getLogger(__name__)


def _configure_logging() -> None:
    paths.ensure_dirs()
    log_path = paths.logs_dir() / "app.log"
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    handler = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    root.addHandler(handler)
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    root.addHandler(console)


class Application:
    def __init__(self, qt_app: QApplication):
        self._qt = qt_app
        self._qt.setApplicationName("Volume Wheel Control")
        self._qt.setOrganizationName("VolumeWheelControl")
        self._qt.setQuitOnLastWindowClosed(False)
        theme.apply_theme()

        self._storage = ConfigStorage(paths.config_path())
        self._config = self._storage.load()
        self._storage.save(self._config)

        self._bus = EventBus()
        self._detector = GestureDetector(
            emit=self._on_gesture,
            timer_factory=QtTimerFactory(),
            double_click_timeout_ms=self._config.settings.double_click_timeout_ms,
            long_press_threshold_ms=self._config.settings.long_press_threshold_ms,
            hold_rotate_window_ms=self._config.settings.hold_rotate_window_ms,
        )
        self._hook = KeyboardHook()
        self._watcher = ForegroundWatcher()

        self._window: MainWindow | None = None
        self._tray = TrayController()

        self._wire_signals()

        if not self._config.settings.paused:
            self._hook.start(
                suppress_mute=self._config.settings.suppress_default_actions
            )
        self._watcher.start()
        self._apply_autostart(self._config.settings.start_with_windows)

        self._tray.set_paused(self._config.settings.paused)
        self._tray.show()

    def _wire_signals(self) -> None:
        self._hook.event.connect(
            self._on_raw_event,
            type=Qt.ConnectionType.QueuedConnection,
        )
        self._tray.openRequested.connect(self._open_window)
        self._tray.pauseToggled.connect(self._on_pause_toggled)
        self._tray.reloadRequested.connect(self._reload)
        self._tray.openConfigFolderRequested.connect(self._open_config_folder)
        self._tray.quitRequested.connect(self._quit)

    def _ensure_window(self) -> MainWindow:
        if self._window is None:
            self._window = MainWindow()
            self._window.apply_config(self._config)
            self._window.bindings_page.saveRequested.connect(self._save_global_bindings)
            self._window.bindings_page.testRequested.connect(self._test_action)
            self._window.profiles_page.saveRequested.connect(self._save_overrides)
            self._window.settings_page.saveRequested.connect(self._save_settings)
            self._window.settings_page.openConfigFolderRequested.connect(
                self._open_config_folder
            )
        return self._window

    def _open_window(self) -> None:
        window = self._ensure_window()
        window.show()
        window.raise_()
        window.activateWindow()

    def _on_raw_event(self, key, event_type) -> None:
        self._detector.handle(key, event_type)

    def _on_gesture(self, gesture: Gesture) -> None:
        context = WindowContext(
            process_name=self._watcher.process_name or None,
            window_title=self._watcher.window_title or None,
        )
        binding = resolve(gesture, context, self._config)
        log.info(
            "Gesture: %s -> %s (process=%s)",
            gesture.value,
            _describe(binding),
            context.process_name,
        )
        try:
            build_action(binding).execute()
        except Exception as exc:
            log.exception("Action execution failed: %s", exc)
        if self._config.settings.show_gesture_hint:
            self._tray.show_message(
                "Volume Wheel Control",
                f"{gesture.value} → {_describe(binding)}",
            )

    def _on_pause_toggled(self, paused: bool) -> None:
        self._config.settings.paused = paused
        self._storage.save(self._config)
        self._hook.set_paused(paused)
        if paused:
            self._hook.stop()
        else:
            self._hook.start(
                suppress_mute=self._config.settings.suppress_default_actions
            )
        self._tray.set_paused(paused)

    def _save_global_bindings(self, bindings: dict) -> None:
        self._config.global_profile.bindings = dict(bindings)
        self._storage.save(self._config)

    def _save_overrides(self, overrides: list[AppOverride]) -> None:
        self._config.app_overrides = list(overrides)
        self._storage.save(self._config)

    def _save_settings(self, settings: Settings) -> None:
        old_suppress = self._config.settings.suppress_default_actions
        self._config.settings = settings
        self._storage.save(self._config)
        self._detector.set_timings(
            settings.double_click_timeout_ms,
            settings.long_press_threshold_ms,
            settings.hold_rotate_window_ms,
        )
        if settings.suppress_default_actions != old_suppress:
            self._hook.restart(suppress_mute=settings.suppress_default_actions)
        if settings.paused:
            self._hook.stop()
        elif not self._hook.is_installed():
            self._hook.start(suppress_mute=settings.suppress_default_actions)
        self._hook.set_paused(settings.paused)
        self._tray.set_paused(settings.paused)
        self._apply_autostart(settings.start_with_windows)

    def _test_action(self, action_cfg: ActionConfig) -> None:
        try:
            build_action(action_cfg).execute()
        except Exception as exc:
            log.warning("Test action failed: %s", exc)

    def _reload(self) -> None:
        self._config = self._storage.load()
        self._detector.set_timings(
            self._config.settings.double_click_timeout_ms,
            self._config.settings.long_press_threshold_ms,
            self._config.settings.hold_rotate_window_ms,
        )
        if self._window is not None:
            self._window.apply_config(self._config)
        self._tray.set_paused(self._config.settings.paused)

    def _open_config_folder(self) -> None:
        folder = paths.appdata_root()
        folder.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(str(folder))
        else:
            subprocess.Popen(["xdg-open", str(folder)])

    def _apply_autostart(self, enabled: bool) -> None:
        executable = _executable_path()
        autostart.set_enabled(enabled, str(executable))

    def _quit(self) -> None:
        self._hook.stop()
        self._watcher.stop()
        self._tray.hide()
        self._qt.quit()


def _describe(action_cfg: ActionConfig) -> str:
    try:
        return build_action(action_cfg).describe()
    except Exception:
        return str(action_cfg)


def _executable_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable)
    return Path(sys.executable)


def run() -> int:
    _configure_logging()
    theme.configure_surface_for_smoothness()
    qt_app = QApplication(sys.argv)
    theme.disable_animations(qt_app)
    application = Application(qt_app)
    qt_app._wheel_app = application
    return qt_app.exec()
