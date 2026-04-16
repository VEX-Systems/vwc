from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFormLayout, QWidget
from qfluentwidgets import ComboBox

from ...config.models import WindowActionConfig


_CHOICES: list[tuple[str, str]] = [
    ("minimize", "Minimize window"),
    ("maximize", "Maximize window"),
    ("restore", "Restore window"),
    ("close", "Close window"),
    ("minimize_all", "Show desktop"),
    ("switch_next", "Switch next window"),
    ("switch_prev", "Switch previous window"),
    ("fullscreen", "Toggle fullscreen"),
]


class WindowEditor(QWidget):
    changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._combo = ComboBox(self)
        for value, label in _CHOICES:
            self._combo.addItem(label, userData=value)
        self._combo.currentIndexChanged.connect(lambda _: self.changed.emit())

        layout = QFormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addRow("Window action", self._combo)

    def set_config(self, config: WindowActionConfig) -> None:
        for i, (value, _label) in enumerate(_CHOICES):
            if value == config.action:
                self._combo.setCurrentIndex(i)
                return
        self._combo.setCurrentIndex(0)

    def get_config(self) -> WindowActionConfig:
        value = self._combo.currentData()
        return WindowActionConfig(action=value)
