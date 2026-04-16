from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import CheckBox, ComboBox, LineEdit, StrongBodyLabel, SubtitleLabel

from ...config.models import AppOverride, MatchRule
from ...gestures.gestures import GESTURE_LABELS, Gesture
from ..editors.action_editor import ActionEditor


_MATCH_TYPES: list[tuple[str, str]] = [
    ("process", "Process name (exact)"),
    ("title_contains", "Window title contains"),
    ("title_regex", "Window title regex"),
]


class OverrideDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, override: AppOverride | None = None):
        super().__init__(parent)
        self.setWindowTitle("App override")
        self.resize(720, 520)
        self.setModal(True)

        self._name = LineEdit(self)
        self._name.setPlaceholderText("Spotify")
        self._match_type = ComboBox(self)
        for value, label in _MATCH_TYPES:
            self._match_type.addItem(label, userData=value)
        self._match_value = LineEdit(self)
        self._match_value.setPlaceholderText("Spotify.exe")

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.addRow("Name", self._name)
        form.addRow("Match type", self._match_type)
        form.addRow("Match value", self._match_value)

        self._gesture_list = QListWidget(self)
        self._gesture_list.setSpacing(2)
        for gesture in Gesture:
            item = QListWidgetItem(GESTURE_LABELS[gesture])
            item.setData(Qt.ItemDataRole.UserRole, gesture.value)
            self._gesture_list.addItem(item)
        self._gesture_list.setCurrentRow(0)
        self._gesture_list.currentRowChanged.connect(self._on_row_changed)

        self._use_global = CheckBox("Use global binding", self)
        self._use_global.stateChanged.connect(self._on_use_global_changed)

        self._editor = ActionEditor(self)
        self._editor_label = StrongBodyLabel(f"Action for {GESTURE_LABELS[Gesture.SINGLE_CLICK]}", self)

        bindings_column = QVBoxLayout()
        bindings_column.addWidget(self._editor_label)
        bindings_column.addWidget(self._use_global)
        bindings_column.addWidget(self._editor, 1)

        body = QHBoxLayout()
        body.setSpacing(16)
        body.addWidget(self._gesture_list, 1)
        body.addLayout(bindings_column, 2)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(12)
        root.addWidget(SubtitleLabel("App override", self))
        root.addWidget(QLabel("Override specific gestures when this app is in focus.", self))
        root.addLayout(form)
        root.addSpacing(8)
        root.addLayout(body, 1)
        root.addWidget(buttons)

        self._bindings: dict[str, object] = {}
        if override is not None:
            self._load(override)

        self._current: Gesture = Gesture.SINGLE_CLICK
        self._refresh_editor()

    def _load(self, override: AppOverride) -> None:
        self._name.setText(override.name)
        for i, (value, _label) in enumerate(_MATCH_TYPES):
            if value == override.match.type:
                self._match_type.setCurrentIndex(i)
                break
        self._match_value.setText(override.match.value)
        self._bindings = dict(override.bindings)

    def _on_row_changed(self, row: int) -> None:
        if row < 0:
            return
        self._current = list(Gesture)[row]
        self._refresh_editor()

    def _refresh_editor(self) -> None:
        self._editor_label.setText(f"Action for {GESTURE_LABELS[self._current]}")
        key = self._current.value
        if key in self._bindings:
            self._use_global.setChecked(False)
            self._editor.setEnabled(True)
            self._editor.set_config(self._bindings[key])
        else:
            self._use_global.setChecked(True)
            self._editor.setEnabled(False)

    def _on_use_global_changed(self) -> None:
        key = self._current.value
        if self._use_global.isChecked():
            self._bindings.pop(key, None)
            self._editor.setEnabled(False)
        else:
            if key not in self._bindings:
                self._bindings[key] = self._editor.get_config()
            self._editor.setEnabled(True)

    def accept(self) -> None:
        if not self._use_global.isChecked():
            try:
                self._bindings[self._current.value] = self._editor.get_config()
            except Exception:
                pass
        super().accept()

    def get_override(self) -> AppOverride:
        if not self._use_global.isChecked():
            try:
                self._bindings[self._current.value] = self._editor.get_config()
            except Exception:
                pass
        return AppOverride(
            name=self._name.text().strip() or "Override",
            match=MatchRule(
                type=self._match_type.currentData(),
                value=self._match_value.text().strip(),
            ),
            bindings=dict(self._bindings),
        )
