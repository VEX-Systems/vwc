from __future__ import annotations

import logging
import sys

from PyQt6.QtCore import QObject, QTimer, pyqtSignal


log = logging.getLogger(__name__)


class ForegroundWatcher(QObject):
    changed = pyqtSignal(str, str)

    def __init__(self, poll_interval_ms: int = 500, parent: QObject | None = None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setInterval(poll_interval_ms)
        self._timer.timeout.connect(self._poll)
        self._process_name: str = ""
        self._window_title: str = ""
        self._available = sys.platform == "win32"
        if self._available:
            try:
                import psutil
                import win32gui
                import win32process

                self._psutil = psutil
                self._win32gui = win32gui
                self._win32process = win32process
            except ImportError as exc:
                log.warning("Foreground watcher disabled: %s", exc)
                self._available = False

    @property
    def process_name(self) -> str:
        return self._process_name

    @property
    def window_title(self) -> str:
        return self._window_title

    def start(self) -> None:
        if not self._available:
            return
        self._poll()
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def _poll(self) -> None:
        if not self._available:
            return
        try:
            hwnd = self._win32gui.GetForegroundWindow()
            if not hwnd:
                return
            title = self._win32gui.GetWindowText(hwnd) or ""
            _, pid = self._win32process.GetWindowThreadProcessId(hwnd)
            process_name = ""
            if pid:
                try:
                    process_name = self._psutil.Process(pid).name()
                except (self._psutil.NoSuchProcess, self._psutil.AccessDenied):
                    process_name = ""
        except Exception as exc:
            log.debug("Foreground poll error: %s", exc)
            return
        if process_name != self._process_name or title != self._window_title:
            self._process_name = process_name
            self._window_title = title
            self.changed.emit(process_name, title)
