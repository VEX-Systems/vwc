from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal

from .gestures.gestures import Gesture
from .input.raw_events import EventType, RawKey


class EventBus(QObject):
    rawEvent = pyqtSignal(object, object)
    gestureDetected = pyqtSignal(object)
    configChanged = pyqtSignal()
    pauseToggled = pyqtSignal(bool)
    foregroundChanged = pyqtSignal(str, str)

    def emit_raw(self, key: RawKey, event: EventType) -> None:
        self.rawEvent.emit(key, event)

    def emit_gesture(self, gesture: Gesture) -> None:
        self.gestureDetected.emit(gesture)
