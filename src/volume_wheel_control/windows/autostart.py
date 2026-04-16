from __future__ import annotations

import logging
import sys


log = logging.getLogger(__name__)


_REGISTRY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = "VolumeWheelControl"


def is_enabled() -> bool:
    if sys.platform != "win32":
        return False
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REGISTRY_PATH) as key:
            winreg.QueryValueEx(key, _VALUE_NAME)
            return True
    except FileNotFoundError:
        return False
    except OSError as exc:
        log.warning("Cannot read autostart key: %s", exc)
        return False


def set_enabled(enabled: bool, executable_path: str) -> None:
    if sys.platform != "win32":
        return
    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _REGISTRY_PATH,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            if enabled:
                command = f'"{executable_path}"'
                winreg.SetValueEx(key, _VALUE_NAME, 0, winreg.REG_SZ, command)
            else:
                try:
                    winreg.DeleteValue(key, _VALUE_NAME)
                except FileNotFoundError:
                    pass
    except OSError as exc:
        log.warning("Cannot write autostart key: %s", exc)
