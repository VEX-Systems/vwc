from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFocusEvent, QKeyEvent
from PyQt6.QtWidgets import QHBoxLayout, QWidget
from qfluentwidgets import LineEdit, PushButton

from ...config.models import HotkeyActionConfig


_MOD_KEYS = {
    Qt.Key.Key_Control,
    Qt.Key.Key_Shift,
    Qt.Key.Key_Alt,
    Qt.Key.Key_Meta,
    Qt.Key.Key_AltGr,
}


def _format_modifiers(modifiers: Qt.KeyboardModifier) -> list[str]:
    parts: list[str] = []
    if modifiers & Qt.KeyboardModifier.ControlModifier:
        parts.append("ctrl")
    if modifiers & Qt.KeyboardModifier.AltModifier:
        parts.append("alt")
    if modifiers & Qt.KeyboardModifier.ShiftModifier:
        parts.append("shift")
    if modifiers & Qt.KeyboardModifier.MetaModifier:
        parts.append("win")
    return parts


class _CaptureLine(LineEdit):
    captured = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._capturing = False
        self.setReadOnly(True)
        self.setPlaceholderText("Click Record and press a combination")

    def start_capture(self) -> None:
        self._capturing = True
        self.setReadOnly(False)
        self.setText("Press keys...")
        self.setFocus(Qt.FocusReason.OtherFocusReason)

    def stop_capture(self) -> None:
        self._capturing = False
        self.setReadOnly(True)

    def focusOutEvent(self, event: QFocusEvent) -> None:
        self.stop_capture()
        super().focusOutEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if not self._capturing:
            super().keyPressEvent(event)
            return
        key = event.key()
        if key in _MOD_KEYS:
            return
        mods = _format_modifiers(event.modifiers())
        name = _normalize_key_name(event)
        if not name:
            return
        parts = mods + [name]
        combo = "+".join(parts)
        self.setText(combo)
        self.captured.emit(combo)
        self.stop_capture()


def _normalize_key_name(event: QKeyEvent) -> str:
    text = event.text()
    if text and text.isprintable() and len(text) == 1 and not text.isspace():
        return text.lower()
    key = event.key()
    names = {
        Qt.Key.Key_Left: "left",
        Qt.Key.Key_Right: "right",
        Qt.Key.Key_Up: "up",
        Qt.Key.Key_Down: "down",
        Qt.Key.Key_Space: "space",
        Qt.Key.Key_Return: "enter",
        Qt.Key.Key_Enter: "enter",
        Qt.Key.Key_Escape: "esc",
        Qt.Key.Key_Tab: "tab",
        Qt.Key.Key_Backspace: "backspace",
        Qt.Key.Key_Delete: "delete",
        Qt.Key.Key_Home: "home",
        Qt.Key.Key_End: "end",
        Qt.Key.Key_PageUp: "page up",
        Qt.Key.Key_PageDown: "page down",
        Qt.Key.Key_Insert: "insert",
    }
    if key in names:
        return names[key]
    for i in range(12):
        if key == getattr(Qt.Key, f"Key_F{i + 1}"):
            return f"f{i + 1}"
    return ""


class HotkeyEditor(QWidget):
    changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._line = _CaptureLine(self)
        self._record = PushButton("Record", self)
        self._clear = PushButton("Clear", self)
        self._record.clicked.connect(self._line.start_capture)
        self._clear.clicked.connect(self._on_clear)
        self._line.captured.connect(lambda _: self.changed.emit())
        self._line.textChanged.connect(lambda _: self.changed.emit())

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._line, 1)
        layout.addWidget(self._record)
        layout.addWidget(self._clear)

    def set_config(self, config: HotkeyActionConfig) -> None:
        self._line.setText(config.keys)

    def get_config(self) -> HotkeyActionConfig:
        text = self._line.text().strip()
        if not text or text.startswith("Press"):
            text = "ctrl"
        return HotkeyActionConfig(keys=text)

    def _on_clear(self) -> None:
        self._line.setText("")
