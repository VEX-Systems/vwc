from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QFormLayout, QHBoxLayout, QWidget
from qfluentwidgets import LineEdit, PushButton

from ...config.models import RunActionConfig


class RunEditor(QWidget):
    changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._path = LineEdit(self)
        self._path.setPlaceholderText(r"C:\Windows\System32\calc.exe")
        self._browse = PushButton("Browse", self)
        self._args = LineEdit(self)
        self._args.setPlaceholderText("Optional arguments")
        self._cwd = LineEdit(self)
        self._cwd.setPlaceholderText("Optional working directory")

        path_row = QHBoxLayout()
        path_row.setContentsMargins(0, 0, 0, 0)
        path_row.addWidget(self._path, 1)
        path_row.addWidget(self._browse)
        path_container = QWidget(self)
        path_container.setLayout(path_row)

        layout = QFormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addRow("Path", path_container)
        layout.addRow("Arguments", self._args)
        layout.addRow("Working dir", self._cwd)

        self._browse.clicked.connect(self._on_browse)
        self._path.textChanged.connect(lambda _: self.changed.emit())
        self._args.textChanged.connect(lambda _: self.changed.emit())
        self._cwd.textChanged.connect(lambda _: self.changed.emit())

    def set_config(self, config: RunActionConfig) -> None:
        self._path.setText(config.path)
        self._args.setText(config.args)
        self._cwd.setText(config.cwd)

    def get_config(self) -> RunActionConfig:
        path = self._path.text().strip() or "cmd.exe"
        return RunActionConfig(
            path=path,
            args=self._args.text().strip(),
            cwd=self._cwd.text().strip(),
        )

    def _on_browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select an executable or file",
            self._path.text() or "",
            "Executables (*.exe);;All files (*.*)",
        )
        if path:
            self._path.setText(path)
