from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import QObject, QTimer

from .timer import TimerHandle


class QtTimerHandle:
    def __init__(self, timer: QTimer):
        self._timer = timer

    def start(self, ms: int) -> None:
        self._timer.start(ms)

    def stop(self) -> None:
        self._timer.stop()

    def is_active(self) -> bool:
        return self._timer.isActive()


class QtTimerFactory:
    def __init__(self, parent: QObject | None = None):
        self._parent = parent

    def create(self, callback: Callable[[], None]) -> TimerHandle:
        timer = QTimer(self._parent)
        timer.setSingleShot(True)
        timer.timeout.connect(callback)
        return QtTimerHandle(timer)
