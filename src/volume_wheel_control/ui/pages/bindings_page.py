from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import CardWidget, PushButton, StrongBodyLabel, SubtitleLabel

from ...actions.registry import build_action
from ...config.models import ActionConfig, Config, NoOpActionConfig
from ...gestures.gestures import GESTURE_LABELS, Gesture
from ..editors.action_editor import ActionEditor


class BindingsPage(QWidget):
    saveRequested = pyqtSignal(object)
    testRequested = pyqtSignal(object)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._config: Config | None = None
        self._working: dict[str, ActionConfig] = {}
        self._current: Gesture = Gesture.SINGLE_CLICK

        self._title = SubtitleLabel("Global Bindings", self)
        self._subtitle = QLabel(
            "Choose what each gesture on the volume knob does.",
            self,
        )
        self._subtitle.setStyleSheet("color: #a0a0a8;")

        self._list = QListWidget(self)
        self._list.setAlternatingRowColors(False)
        self._list.setSpacing(2)
        for gesture in Gesture:
            item = QListWidgetItem(GESTURE_LABELS[gesture])
            item.setData(Qt.ItemDataRole.UserRole, gesture.value)
            self._list.addItem(item)
        self._list.setCurrentRow(0)
        self._list.currentRowChanged.connect(self._on_row_changed)

        self._editor_card = CardWidget(self)
        card_layout = QVBoxLayout(self._editor_card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(12)

        self._editor_title = StrongBodyLabel("Action for Single click", self._editor_card)
        self._editor = ActionEditor(self._editor_card)
        self._editor.changed.connect(self._on_editor_changed)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        self._test_btn = PushButton("Test", self._editor_card)
        self._save_btn = PushButton("Save", self._editor_card)
        self._save_btn.setEnabled(False)
        self._test_btn.clicked.connect(self._on_test)
        self._save_btn.clicked.connect(self._on_save)
        button_row.addWidget(self._test_btn)
        button_row.addWidget(self._save_btn)

        card_layout.addWidget(self._editor_title)
        card_layout.addWidget(self._editor, 1)
        card_layout.addLayout(button_row)

        body = QHBoxLayout()
        body.setSpacing(16)
        body.addWidget(self._list, 1)
        body.addWidget(self._editor_card, 2)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(6)
        root.addWidget(self._title)
        root.addWidget(self._subtitle)
        root.addSpacing(12)
        root.addLayout(body, 1)

    def set_config(self, config: Config) -> None:
        self._config = config
        self._working = {}
        for gesture in Gesture:
            self._working[gesture.value] = config.global_profile.get(gesture.value)
        self._refresh_labels()
        self._load_current()
        self._save_btn.setEnabled(False)

    def _on_row_changed(self, row: int) -> None:
        if row < 0:
            return
        gestures = list(Gesture)
        self._current = gestures[row]
        self._load_current()

    def _load_current(self) -> None:
        self._editor_title.setText(f"Action for {GESTURE_LABELS[self._current]}")
        if self._current.value in self._working:
            self._editor.set_config(self._working[self._current.value])

    def _on_editor_changed(self) -> None:
        try:
            cfg = self._editor.get_config()
        except Exception:
            return
        self._working[self._current.value] = cfg
        self._refresh_labels()
        self._save_btn.setEnabled(True)

    def _refresh_labels(self) -> None:
        for i, gesture in enumerate(Gesture):
            summary = _summary(self._working.get(gesture.value))
            label = f"{GESTURE_LABELS[gesture]}   —   {summary}"
            item = self._list.item(i)
            if item is not None:
                item.setText(label)

    def _on_test(self) -> None:
        try:
            cfg = self._editor.get_config()
        except Exception:
            return
        self.testRequested.emit(cfg)

    def _on_save(self) -> None:
        self.saveRequested.emit(dict(self._working))
        self._save_btn.setEnabled(False)


def _summary(cfg: ActionConfig | None) -> str:
    if cfg is None or isinstance(cfg, NoOpActionConfig):
        return "Disabled"
    try:
        return build_action(cfg).describe()
    except Exception:
        return "—"
