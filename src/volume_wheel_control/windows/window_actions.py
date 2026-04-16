from __future__ import annotations

import logging
import sys


log = logging.getLogger(__name__)


if sys.platform == "win32":
    import win32con
    import win32gui
else:
    win32gui = None
    win32con = None


def _foreground_hwnd() -> int | None:
    if win32gui is None:
        return None
    hwnd = win32gui.GetForegroundWindow()
    return hwnd or None


def minimize_foreground() -> None:
    hwnd = _foreground_hwnd()
    if hwnd is None or win32gui is None:
        log.warning("No foreground window to minimize")
        return
    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)


def maximize_foreground() -> None:
    hwnd = _foreground_hwnd()
    if hwnd is None or win32gui is None:
        return
    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)


def restore_foreground() -> None:
    hwnd = _foreground_hwnd()
    if hwnd is None or win32gui is None:
        return
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)


def close_foreground() -> None:
    hwnd = _foreground_hwnd()
    if hwnd is None or win32gui is None:
        return
    win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
