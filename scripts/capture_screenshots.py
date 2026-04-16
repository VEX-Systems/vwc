from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from volume_wheel_control.config.defaults import default_config
from volume_wheel_control.config.models import (
    AppOverride,
    HotkeyActionConfig,
    MatchRule,
    MediaActionConfig,
    RunActionConfig,
    WindowActionConfig,
)
from volume_wheel_control.ui import theme
from volume_wheel_control.ui.dialogs.override_dialog import OverrideDialog
from volume_wheel_control.ui.main_window import MainWindow


def _sample_config():
    cfg = default_config()
    cfg.global_profile.bindings["single_click"] = MediaActionConfig(key="mute")
    cfg.global_profile.bindings["double_click"] = MediaActionConfig(key="next_track")
    cfg.global_profile.bindings["triple_click"] = MediaActionConfig(key="previous_track")
    cfg.global_profile.bindings["quadruple_click"] = HotkeyActionConfig(keys="ctrl+shift+n")
    cfg.global_profile.bindings["long_press"] = MediaActionConfig(key="play_pause")
    cfg.global_profile.bindings["hold_rotate_up"] = HotkeyActionConfig(keys="ctrl+tab")
    cfg.global_profile.bindings["hold_rotate_down"] = HotkeyActionConfig(keys="ctrl+shift+tab")
    cfg.app_overrides = [
        AppOverride(
            name="Spotify",
            match=MatchRule(type="process", value="Spotify.exe"),
            bindings={
                "double_click": HotkeyActionConfig(keys="ctrl+right"),
                "long_press": MediaActionConfig(key="play_pause"),
            },
        ),
        AppOverride(
            name="Visual Studio Code",
            match=MatchRule(type="process", value="Code.exe"),
            bindings={
                "long_press": HotkeyActionConfig(keys="ctrl+shift+p"),
                "quadruple_click": RunActionConfig(path="C:\\Windows\\System32\\cmd.exe"),
            },
        ),
        AppOverride(
            name="YouTube",
            match=MatchRule(type="title_contains", value="YouTube"),
            bindings={
                "long_press": HotkeyActionConfig(keys="space"),
                "double_click": HotkeyActionConfig(keys="f"),
                "hold_rotate_up": HotkeyActionConfig(keys="l"),
                "hold_rotate_down": HotkeyActionConfig(keys="j"),
            },
        ),
    ]
    return cfg


def capture(window: MainWindow, out: Path) -> None:
    app = QApplication.instance()
    for _ in range(8):
        app.processEvents()
    pixmap = window.grab()
    pixmap.save(str(out))
    print(f"wrote {out}")


def main() -> int:
    app = QApplication(sys.argv)
    theme.apply_theme()
    theme.disable_animations(app)

    window = MainWindow()
    window.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    window.apply_config(_sample_config())
    window.resize(1180, 760)
    window.show()
    for _ in range(12):
        app.processEvents()

    out_dir = ROOT / "docs" / "images"
    out_dir.mkdir(parents=True, exist_ok=True)

    pages = [
        (window.bindings_page, "bindings"),
        (window.profiles_page, "profiles"),
        (window.settings_page, "settings"),
        (window.about_page, "about"),
    ]

    for page, name in pages:
        try:
            window.switchTo(page)
        except AttributeError:
            window.stackedWidget.setCurrentWidget(page)
        for _ in range(12):
            app.processEvents()
        capture(window, out_dir / f"{name}.png")

    dialog = OverrideDialog(parent=window, override=_sample_config().app_overrides[2])
    dialog.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    dialog.resize(780, 560)
    dialog.show()
    for _ in range(12):
        app.processEvents()
    dialog.grab().save(str(out_dir / "override_dialog.png"))
    print(f"wrote {out_dir / 'override_dialog.png'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
