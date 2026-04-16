from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    CardWidget,
    PushButton,
    Slider,
    StrongBodyLabel,
    SubtitleLabel,
    SwitchButton,
)

from ...config.models import Config, Settings


class SettingsPage(QWidget):
    saveRequested = pyqtSignal(object)
    openConfigFolderRequested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._settings: Settings | None = None

        self._dbl_slider = Slider()
        self._dbl_slider.setRange(100, 500)
        self._dbl_value = QLabel()

        self._long_slider = Slider()
        self._long_slider.setRange(300, 1000)
        self._long_value = QLabel()

        self._hold_rotate_slider = Slider()
        self._hold_rotate_slider.setRange(200, 2000)
        self._hold_rotate_value = QLabel()

        self._suppress_switch = SwitchButton()
        self._autostart_switch = SwitchButton()
        self._pause_switch = SwitchButton()

        self._open_folder_btn = PushButton("Open config folder")
        self._save_btn = PushButton("Save")
        self._save_btn.setEnabled(False)

        self._dbl_slider.valueChanged.connect(self._on_dbl_changed)
        self._long_slider.valueChanged.connect(self._on_long_changed)
        self._hold_rotate_slider.valueChanged.connect(self._on_hold_rotate_changed)
        self._suppress_switch.checkedChanged.connect(lambda _: self._mark_dirty())
        self._autostart_switch.checkedChanged.connect(lambda _: self._mark_dirty())
        self._pause_switch.checkedChanged.connect(lambda _: self._mark_dirty())
        self._open_folder_btn.clicked.connect(self.openConfigFolderRequested.emit)
        self._save_btn.clicked.connect(self._on_save)

        title = SubtitleLabel("Settings", self)
        subtitle = QLabel("Fine-tune timing, startup and detection.", self)
        subtitle.setStyleSheet("color: #a0a0a8;")

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(6)
        root.addWidget(title)
        root.addWidget(subtitle)
        root.addSpacing(12)

        root.addWidget(
            _labeled_slider_card(
                "Double-click window",
                "Time the app waits after a click before deciding single vs double.",
                self._dbl_slider,
                self._dbl_value,
                suffix=" ms",
            )
        )
        root.addWidget(
            _labeled_slider_card(
                "Long-press threshold",
                "How long the knob has to be held for a long-press gesture.",
                self._long_slider,
                self._long_value,
                suffix=" ms",
            )
        )
        root.addWidget(
            _labeled_slider_card(
                "Click + rotate window",
                "After a click, how long the app waits for a rotation to turn it into a 'click + rotate' combo.",
                self._hold_rotate_slider,
                self._hold_rotate_value,
                suffix=" ms",
            )
        )
        root.addWidget(
            _labeled_toggle_card(
                "Suppress default mute",
                "Block Windows from muting immediately so double and triple click can trigger. "
                "Single click mute will be slightly delayed.",
                self._suppress_switch,
            )
        )
        root.addWidget(
            _labeled_toggle_card(
                "Start with Windows",
                "Launch Volume Wheel Control when you sign in.",
                self._autostart_switch,
            )
        )
        root.addWidget(
            _labeled_toggle_card(
                "Pause detection",
                "Temporarily stop reacting to the volume knob.",
                self._pause_switch,
            )
        )

        footer = QHBoxLayout()
        footer.addWidget(self._open_folder_btn)
        footer.addStretch(1)
        footer.addWidget(self._save_btn)
        root.addSpacing(8)
        root.addLayout(footer)
        root.addStretch(1)

    def set_config(self, config: Config) -> None:
        self._settings = config.settings
        self._dbl_slider.setValue(config.settings.double_click_timeout_ms)
        self._long_slider.setValue(config.settings.long_press_threshold_ms)
        self._hold_rotate_slider.setValue(config.settings.hold_rotate_window_ms)
        self._suppress_switch.setChecked(config.settings.suppress_default_actions)
        self._autostart_switch.setChecked(config.settings.start_with_windows)
        self._pause_switch.setChecked(config.settings.paused)
        self._dbl_value.setText(f"{self._dbl_slider.value()} ms")
        self._long_value.setText(f"{self._long_slider.value()} ms")
        self._hold_rotate_value.setText(f"{self._hold_rotate_slider.value()} ms")
        self._save_btn.setEnabled(False)

    def _on_dbl_changed(self, value: int) -> None:
        self._dbl_value.setText(f"{value} ms")
        self._mark_dirty()

    def _on_long_changed(self, value: int) -> None:
        self._long_value.setText(f"{value} ms")
        self._mark_dirty()

    def _on_hold_rotate_changed(self, value: int) -> None:
        self._hold_rotate_value.setText(f"{value} ms")
        self._mark_dirty()

    def _mark_dirty(self) -> None:
        self._save_btn.setEnabled(True)

    def _on_save(self) -> None:
        new_settings = Settings(
            double_click_timeout_ms=self._dbl_slider.value(),
            long_press_threshold_ms=self._long_slider.value(),
            hold_rotate_window_ms=self._hold_rotate_slider.value(),
            suppress_default_actions=self._suppress_switch.isChecked(),
            start_with_windows=self._autostart_switch.isChecked(),
            paused=self._pause_switch.isChecked(),
            show_gesture_hint=self._settings.show_gesture_hint if self._settings else False,
        )
        self.saveRequested.emit(new_settings)
        self._save_btn.setEnabled(False)


def _labeled_slider_card(
    title: str,
    description: str,
    slider: Slider,
    value_label: QLabel,
    suffix: str = "",
) -> CardWidget:
    card = CardWidget()
    layout = QVBoxLayout(card)
    layout.setContentsMargins(18, 14, 18, 14)
    layout.setSpacing(6)
    header = QHBoxLayout()
    header.addWidget(StrongBodyLabel(title, card))
    header.addStretch(1)
    header.addWidget(value_label)
    value_label.setStyleSheet("color: #c0c0cc;")
    desc = QLabel(description, card)
    desc.setWordWrap(True)
    desc.setStyleSheet("color: #9a9aa5;")
    layout.addLayout(header)
    layout.addWidget(desc)
    layout.addWidget(slider)
    return card


def _labeled_toggle_card(title: str, description: str, switch: SwitchButton) -> CardWidget:
    card = CardWidget()
    layout = QHBoxLayout(card)
    layout.setContentsMargins(18, 14, 18, 14)
    layout.setSpacing(12)
    text_col = QVBoxLayout()
    text_col.setSpacing(2)
    text_col.addWidget(StrongBodyLabel(title, card))
    desc = QLabel(description, card)
    desc.setWordWrap(True)
    desc.setStyleSheet("color: #9a9aa5;")
    text_col.addWidget(desc)
    layout.addLayout(text_col, 1)
    layout.addWidget(switch)
    return card
