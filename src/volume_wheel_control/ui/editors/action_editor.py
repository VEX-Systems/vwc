from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget
from qfluentwidgets import ComboBox

from ...config.models import (
    ActionConfig,
    HotkeyActionConfig,
    MediaActionConfig,
    NoOpActionConfig,
    RunActionConfig,
    WindowActionConfig,
)
from .hotkey_editor import HotkeyEditor
from .media_editor import MediaEditor
from .run_editor import RunEditor
from .window_editor import WindowEditor


_TYPES: list[tuple[str, str]] = [
    ("media", "Media key"),
    ("hotkey", "Hotkey"),
    ("run", "Run program"),
    ("window", "Window action"),
    ("none", "Disabled"),
]


class ActionEditor(QWidget):
    changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self._type_combo = ComboBox(self)
        for value, label in _TYPES:
            self._type_combo.addItem(label, userData=value)

        self._stack = QStackedWidget(self)
        self._media = MediaEditor(self)
        self._hotkey = HotkeyEditor(self)
        self._run = RunEditor(self)
        self._window = WindowEditor(self)
        self._disabled = QWidget(self)

        self._stack.addWidget(self._media)
        self._stack.addWidget(self._hotkey)
        self._stack.addWidget(self._run)
        self._stack.addWidget(self._window)
        self._stack.addWidget(self._disabled)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addWidget(self._type_combo)
        layout.addWidget(self._stack, 1)

        self._type_combo.currentIndexChanged.connect(self._on_type_changed)
        self._media.changed.connect(self.changed.emit)
        self._hotkey.changed.connect(self.changed.emit)
        self._run.changed.connect(self.changed.emit)
        self._window.changed.connect(self.changed.emit)

    def set_config(self, config: ActionConfig) -> None:
        self.blockSignals(True)
        if isinstance(config, MediaActionConfig):
            self._type_combo.setCurrentIndex(0)
            self._media.set_config(config)
            self._stack.setCurrentIndex(0)
        elif isinstance(config, HotkeyActionConfig):
            self._type_combo.setCurrentIndex(1)
            self._hotkey.set_config(config)
            self._stack.setCurrentIndex(1)
        elif isinstance(config, RunActionConfig):
            self._type_combo.setCurrentIndex(2)
            self._run.set_config(config)
            self._stack.setCurrentIndex(2)
        elif isinstance(config, WindowActionConfig):
            self._type_combo.setCurrentIndex(3)
            self._window.set_config(config)
            self._stack.setCurrentIndex(3)
        else:
            self._type_combo.setCurrentIndex(4)
            self._stack.setCurrentIndex(4)
        self.blockSignals(False)

    def get_config(self) -> ActionConfig:
        index = self._stack.currentIndex()
        if index == 0:
            return self._media.get_config()
        if index == 1:
            return self._hotkey.get_config()
        if index == 2:
            return self._run.get_config()
        if index == 3:
            return self._window.get_config()
        return NoOpActionConfig()

    def _on_type_changed(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        self.changed.emit()
