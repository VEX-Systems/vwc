from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

from . import theme


class TrayController(QObject):
    openRequested = pyqtSignal()
    pauseToggled = pyqtSignal(bool)
    reloadRequested = pyqtSignal()
    openConfigFolderRequested = pyqtSignal()
    quitRequested = pyqtSignal()

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._tray = QSystemTrayIcon(theme.tray_icon(active=True), parent)
        self._tray.setToolTip("Volume Wheel Control")
        self._menu = QMenu()

        self._action_open = QAction("Open", self._menu)
        self._action_pause = QAction("Pause detection", self._menu)
        self._action_pause.setCheckable(True)
        self._action_reload = QAction("Reload config", self._menu)
        self._action_config_folder = QAction("Open config folder", self._menu)
        self._action_quit = QAction("Quit", self._menu)

        self._menu.addAction(self._action_open)
        self._menu.addAction(self._action_pause)
        self._menu.addSeparator()
        self._menu.addAction(self._action_reload)
        self._menu.addAction(self._action_config_folder)
        self._menu.addSeparator()
        self._menu.addAction(self._action_quit)

        self._tray.setContextMenu(self._menu)

        self._action_open.triggered.connect(self.openRequested.emit)
        self._action_pause.toggled.connect(self.pauseToggled.emit)
        self._action_reload.triggered.connect(self.reloadRequested.emit)
        self._action_config_folder.triggered.connect(self.openConfigFolderRequested.emit)
        self._action_quit.triggered.connect(self.quitRequested.emit)
        self._tray.activated.connect(self._on_activated)

    def show(self) -> None:
        self._tray.show()

    def hide(self) -> None:
        self._tray.hide()

    def set_paused(self, paused: bool) -> None:
        if self._action_pause.isChecked() != paused:
            self._action_pause.blockSignals(True)
            self._action_pause.setChecked(paused)
            self._action_pause.blockSignals(False)
        self._tray.setIcon(theme.tray_icon(active=not paused))

    def show_message(self, title: str, body: str) -> None:
        self._tray.showMessage(title, body, theme.tray_icon(active=True), 1500)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.openRequested.emit()
