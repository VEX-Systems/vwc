from __future__ import annotations

import ctypes
import logging
import threading
from ctypes import wintypes

from PyQt6.QtCore import QObject, pyqtSignal

from .raw_events import EventType, RawKey


log = logging.getLogger(__name__)


VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
WM_QUIT = 0x0012

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001

SELF_EXTRA_INFO = 0x56574302


_VK_TO_RAW: dict[int, RawKey] = {
    VK_VOLUME_MUTE: RawKey.MUTE,
    VK_VOLUME_UP: RawKey.VOLUME_UP,
    VK_VOLUME_DOWN: RawKey.VOLUME_DOWN,
}


class _KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class _HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("ki", _KEYBDINPUT),
        ("mi", _MOUSEINPUT),
        ("hi", _HARDWAREINPUT),
    ]


class _INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("u", _INPUT_UNION),
    ]


_user32 = ctypes.WinDLL("user32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

_LowLevelKeyboardProc = ctypes.WINFUNCTYPE(
    ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
)

_user32.SetWindowsHookExW.restype = wintypes.HHOOK
_user32.SetWindowsHookExW.argtypes = [
    ctypes.c_int,
    _LowLevelKeyboardProc,
    wintypes.HINSTANCE,
    wintypes.DWORD,
]
_user32.UnhookWindowsHookEx.restype = wintypes.BOOL
_user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
_user32.CallNextHookEx.restype = ctypes.c_long
_user32.CallNextHookEx.argtypes = [
    wintypes.HHOOK,
    ctypes.c_int,
    wintypes.WPARAM,
    wintypes.LPARAM,
]
_user32.GetMessageW.argtypes = [
    ctypes.POINTER(wintypes.MSG),
    wintypes.HWND,
    wintypes.UINT,
    wintypes.UINT,
]
_user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
_user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
_user32.PostThreadMessageW.argtypes = [
    wintypes.DWORD,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
]
_user32.SendInput.restype = wintypes.UINT
_user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(_INPUT), ctypes.c_int]
_kernel32.GetModuleHandleW.restype = wintypes.HMODULE
_kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
_kernel32.GetCurrentThreadId.restype = wintypes.DWORD
_kernel32.GetCurrentThreadId.argtypes = []


class KeyboardHook(QObject):
    event = pyqtSignal(object, object)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._suppress_mute = True
        self._paused = False
        self._installed = False
        self._thread: threading.Thread | None = None
        self._thread_id: int = 0
        self._hook_handle: int = 0
        self._proc_ref: _LowLevelKeyboardProc | None = None
        self._lock = threading.Lock()

    def start(self, suppress_mute: bool = True) -> None:
        with self._lock:
            if self._installed:
                return
            self._suppress_mute = suppress_mute
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
            self._installed = True
            log.info("Keyboard hook starting (suppress_mute=%s)", suppress_mute)

    def stop(self) -> None:
        with self._lock:
            if not self._installed:
                return
            tid = self._thread_id
        if tid:
            _user32.PostThreadMessageW(tid, WM_QUIT, 0, 0)
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        with self._lock:
            self._installed = False
            self._thread = None
            self._thread_id = 0
            self._hook_handle = 0
            self._proc_ref = None

    def restart(self, suppress_mute: bool) -> None:
        self.stop()
        self.start(suppress_mute=suppress_mute)

    def set_paused(self, paused: bool) -> None:
        self._paused = paused

    def is_installed(self) -> bool:
        return self._installed

    def _run(self) -> None:
        self._thread_id = _kernel32.GetCurrentThreadId()

        def proc(nCode: int, wParam: int, lParam: int) -> int:
            if nCode < 0:
                return _user32.CallNextHookEx(0, nCode, wParam, lParam)
            try:
                kbd = ctypes.cast(lParam, ctypes.POINTER(_KBDLLHOOKSTRUCT))[0]
                extra = kbd.dwExtraInfo or 0
                if extra == SELF_EXTRA_INFO:
                    return _user32.CallNextHookEx(0, nCode, wParam, lParam)
                vk = int(kbd.vkCode)
                raw = _VK_TO_RAW.get(vk)
                if raw is None:
                    return _user32.CallNextHookEx(0, nCode, wParam, lParam)
                if self._paused:
                    return _user32.CallNextHookEx(0, nCode, wParam, lParam)
                is_down = wParam in (WM_KEYDOWN, WM_SYSKEYDOWN)
                event_type = EventType.DOWN if is_down else EventType.UP
                try:
                    self.event.emit(raw, event_type)
                except Exception as exc:
                    log.exception("Raw event emit failed: %s", exc)
                if raw is RawKey.MUTE and self._suppress_mute:
                    return 1
                if raw in (RawKey.VOLUME_UP, RawKey.VOLUME_DOWN):
                    return 1
            except Exception as exc:
                log.exception("Hook proc error: %s", exc)
            return _user32.CallNextHookEx(0, nCode, wParam, lParam)

        callback = _LowLevelKeyboardProc(proc)
        self._proc_ref = callback
        h_module = _kernel32.GetModuleHandleW(None)
        self._hook_handle = _user32.SetWindowsHookExW(
            WH_KEYBOARD_LL, callback, h_module, 0
        )
        if not self._hook_handle:
            err = ctypes.get_last_error()
            log.error("SetWindowsHookExW failed (error=%d)", err)
            return
        log.info("Keyboard hook installed (handle=%s)", self._hook_handle)

        msg = wintypes.MSG()
        try:
            while True:
                result = _user32.GetMessageW(ctypes.byref(msg), 0, 0, 0)
                if result <= 0:
                    break
                _user32.TranslateMessage(ctypes.byref(msg))
                _user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            _user32.UnhookWindowsHookEx(self._hook_handle)
            log.info("Keyboard hook removed")


def send_media_key(vk: int) -> None:
    is_extended = vk in (VK_VOLUME_MUTE, VK_VOLUME_UP, VK_VOLUME_DOWN, 0xB0, 0xB1, 0xB2, 0xB3)
    flags_base = KEYEVENTF_EXTENDEDKEY if is_extended else 0
    inputs = (_INPUT * 2)()
    inputs[0].type = INPUT_KEYBOARD
    inputs[0].ki = _KEYBDINPUT(
        wVk=vk,
        wScan=0,
        dwFlags=flags_base,
        time=0,
        dwExtraInfo=SELF_EXTRA_INFO,
    )
    inputs[1].type = INPUT_KEYBOARD
    inputs[1].ki = _KEYBDINPUT(
        wVk=vk,
        wScan=0,
        dwFlags=flags_base | KEYEVENTF_KEYUP,
        time=0,
        dwExtraInfo=SELF_EXTRA_INFO,
    )
    _user32.SendInput(2, inputs, ctypes.sizeof(_INPUT))


def send_key_combo(vks: list[int]) -> None:
    n = len(vks)
    if n == 0:
        return
    inputs = (_INPUT * (n * 2))()
    for i, vk in enumerate(vks):
        inputs[i].type = INPUT_KEYBOARD
        inputs[i].ki = _KEYBDINPUT(
            wVk=vk,
            wScan=0,
            dwFlags=0,
            time=0,
            dwExtraInfo=SELF_EXTRA_INFO,
        )
    for i, vk in enumerate(reversed(vks)):
        idx = n + i
        inputs[idx].type = INPUT_KEYBOARD
        inputs[idx].ki = _KEYBDINPUT(
            wVk=vk,
            wScan=0,
            dwFlags=KEYEVENTF_KEYUP,
            time=0,
            dwExtraInfo=SELF_EXTRA_INFO,
        )
    _user32.SendInput(n * 2, inputs, ctypes.sizeof(_INPUT))
