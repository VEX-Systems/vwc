from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
from qfluentwidgets import CardWidget, StrongBodyLabel, SubtitleLabel

from ... import __version__


class AboutPage(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        title = SubtitleLabel("About", self)

        card = CardWidget(self)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(6)
        card_layout.addWidget(StrongBodyLabel(f"Volume Wheel Control {__version__}", card))

        description = QLabel(
            "Programmable macros for keyboard volume knobs. "
            "Map clicks and rotation to media keys, hotkeys, app launchers and window actions. "
            "Assign different macros per application.",
            card,
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #a0a0a8;")
        card_layout.addWidget(description)

        hint = QLabel(
            "Tested on Windows 11 with Ajazz AK820. "
            "Works with any keyboard that emits standard Volume Up / Down / Mute events.",
            card,
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #80808a; font-size: 12px;")
        card_layout.addWidget(hint)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(12)
        root.addWidget(title)
        root.addWidget(card)
        root.addStretch(1)
