from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    CardWidget,
    PushButton,
    StrongBodyLabel,
    SubtitleLabel,
    TransparentToolButton,
    FluentIcon,
)

from ...config.models import AppOverride, Config
from ..dialogs.override_dialog import OverrideDialog


class ProfilesPage(QWidget):
    saveRequested = pyqtSignal(list)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._overrides: list[AppOverride] = []

        self._title = SubtitleLabel("App overrides", self)
        self._subtitle = QLabel(
            "Use different gestures in specific apps. The first match wins.",
            self,
        )
        self._subtitle.setStyleSheet("color: #a0a0a8;")

        self._add_btn = PushButton("Add override", self)
        self._add_btn.clicked.connect(self._on_add)

        self._container = QWidget(self)
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setContentsMargins(0, 0, 0, 0)
        self._container_layout.setSpacing(10)
        self._container_layout.addStretch(1)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(self._container)

        top_row = QHBoxLayout()
        top_row.addWidget(self._title)
        top_row.addStretch(1)
        top_row.addWidget(self._add_btn)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(6)
        root.addLayout(top_row)
        root.addWidget(self._subtitle)
        root.addSpacing(12)
        root.addWidget(scroll, 1)

    def set_config(self, config: Config) -> None:
        self._overrides = list(config.app_overrides)
        self._rebuild()

    def _rebuild(self) -> None:
        while self._container_layout.count() > 0:
            item = self._container_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        if not self._overrides:
            empty = _EmptyState(self._container)
            self._container_layout.addWidget(empty)
        else:
            for idx, override in enumerate(self._overrides):
                card = _OverrideCard(override, self._container)
                card.editRequested.connect(lambda i=idx: self._on_edit(i))
                card.deleteRequested.connect(lambda i=idx: self._on_delete(i))
                self._container_layout.addWidget(card)
        self._container_layout.addStretch(1)

    def _on_add(self) -> None:
        dialog = OverrideDialog(self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self._overrides.append(dialog.get_override())
            self._emit_save()
            self._rebuild()

    def _on_edit(self, index: int) -> None:
        if index >= len(self._overrides):
            return
        dialog = OverrideDialog(self, self._overrides[index])
        if dialog.exec() == dialog.DialogCode.Accepted:
            self._overrides[index] = dialog.get_override()
            self._emit_save()
            self._rebuild()

    def _on_delete(self, index: int) -> None:
        if index >= len(self._overrides):
            return
        self._overrides.pop(index)
        self._emit_save()
        self._rebuild()

    def _emit_save(self) -> None:
        self.saveRequested.emit(list(self._overrides))


class _OverrideCard(CardWidget):
    editRequested = pyqtSignal()
    deleteRequested = pyqtSignal()

    def __init__(self, override: AppOverride, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedHeight(80)

        name = StrongBodyLabel(override.name, self)
        match_text = f"{_match_label(override.match.type)}: {override.match.value or '(empty)'}"
        match_label = QLabel(match_text, self)
        match_label.setStyleSheet("color: #9a9aa5;")

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.addWidget(name)
        text_col.addWidget(match_label)

        count_label = QLabel(f"{len(override.bindings)} custom", self)
        count_label.setStyleSheet("color: #a0a0a8;")

        edit_btn = PushButton("Edit", self)
        del_btn = TransparentToolButton(FluentIcon.DELETE, self)
        edit_btn.clicked.connect(self.editRequested.emit)
        del_btn.clicked.connect(self.deleteRequested.emit)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 10, 10, 10)
        layout.setSpacing(14)
        layout.addLayout(text_col, 1)
        layout.addWidget(count_label)
        layout.addWidget(edit_btn)
        layout.addWidget(del_btn)


class _EmptyState(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        label = QLabel(
            "No app overrides yet. Click Add override to bind different gestures for a specific app.",
            self,
        )
        label.setWordWrap(True)
        label.setStyleSheet("color: #8a8a95; padding: 24px;")
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label)


def _match_label(value: str) -> str:
    labels = {
        "process": "Process",
        "title_contains": "Title contains",
        "title_regex": "Title regex",
    }
    return labels.get(value, value)
