from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFormLayout, QWidget
from qfluentwidgets import ComboBox

from ...config.models import MediaActionConfig


_CHOICES: list[tuple[str, str]] = [
    ("play_pause", "Play / Pause"),
    ("next_track", "Next track"),
    ("previous_track", "Previous track"),
    ("stop", "Stop"),
    ("mute", "Mute"),
    ("volume_up", "Volume up"),
    ("volume_down", "Volume down"),
]


class MediaEditor(QWidget):
    changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._combo = ComboBox(self)
        for value, label in _CHOICES:
            self._combo.addItem(label, userData=value)
        self._combo.currentIndexChanged.connect(lambda _: self.changed.emit())

        layout = QFormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addRow("Media key", self._combo)

    def set_config(self, config: MediaActionConfig) -> None:
        for i, (value, _label) in enumerate(_CHOICES):
            if value == config.key:
                self._combo.setCurrentIndex(i)
                return
        self._combo.setCurrentIndex(0)

    def get_config(self) -> MediaActionConfig:
        value = self._combo.currentData()
        return MediaActionConfig(key=value)
