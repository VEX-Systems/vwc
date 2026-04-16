from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QCloseEvent
from qfluentwidgets import FluentIcon, FluentWindow

from ..config.models import Config
from . import theme
from .pages.about_page import AboutPage
from .pages.bindings_page import BindingsPage
from .pages.profiles_page import ProfilesPage
from .pages.settings_page import SettingsPage


class MainWindow(FluentWindow):
    closedToTray = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Volume Wheel Control")
        self.setWindowIcon(theme.app_icon())
        self.resize(980, 640)
        try:
            self.setMicaEffectEnabled(False)
        except AttributeError:
            pass

        self.bindings_page = BindingsPage()
        self.bindings_page.setObjectName("bindings")
        self.profiles_page = ProfilesPage()
        self.profiles_page.setObjectName("profiles")
        self.settings_page = SettingsPage()
        self.settings_page.setObjectName("settings")
        self.about_page = AboutPage()
        self.about_page.setObjectName("about")

        self.addSubInterface(self.bindings_page, FluentIcon.MEDIA, "Bindings")
        self.addSubInterface(self.profiles_page, FluentIcon.APPLICATION, "Profiles")
        self.addSubInterface(self.settings_page, FluentIcon.SETTING, "Settings")
        self.addSubInterface(self.about_page, FluentIcon.INFO, "About")

    def apply_config(self, config: Config) -> None:
        self.bindings_page.set_config(config)
        self.profiles_page.set_config(config)
        self.settings_page.set_config(config)

    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()
        self.hide()
        self.closedToTray.emit()
