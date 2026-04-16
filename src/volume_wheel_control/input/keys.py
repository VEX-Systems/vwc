from __future__ import annotations


VK_BACK = 0x08
VK_TAB = 0x09
VK_RETURN = 0x0D
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_PAUSE = 0x13
VK_CAPITAL = 0x14
VK_ESCAPE = 0x1B
VK_SPACE = 0x20
VK_PRIOR = 0x21
VK_NEXT = 0x22
VK_END = 0x23
VK_HOME = 0x24
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_INSERT = 0x2D
VK_DELETE = 0x2E
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_APPS = 0x5D
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_UP = 0xAF
VK_VOLUME_DOWN = 0xAE


_NAME_TO_VK: dict[str, int] = {
    "backspace": VK_BACK,
    "tab": VK_TAB,
    "enter": VK_RETURN,
    "return": VK_RETURN,
    "shift": VK_SHIFT,
    "ctrl": VK_CONTROL,
    "control": VK_CONTROL,
    "alt": VK_MENU,
    "menu": VK_MENU,
    "pause": VK_PAUSE,
    "caps": VK_CAPITAL,
    "capslock": VK_CAPITAL,
    "esc": VK_ESCAPE,
    "escape": VK_ESCAPE,
    "space": VK_SPACE,
    "page up": VK_PRIOR,
    "pageup": VK_PRIOR,
    "pgup": VK_PRIOR,
    "page down": VK_NEXT,
    "pagedown": VK_NEXT,
    "pgdn": VK_NEXT,
    "end": VK_END,
    "home": VK_HOME,
    "left": VK_LEFT,
    "up": VK_UP,
    "right": VK_RIGHT,
    "down": VK_DOWN,
    "insert": VK_INSERT,
    "ins": VK_INSERT,
    "delete": VK_DELETE,
    "del": VK_DELETE,
    "win": VK_LWIN,
    "windows": VK_LWIN,
    "super": VK_LWIN,
    "meta": VK_LWIN,
    "lwin": VK_LWIN,
    "rwin": VK_RWIN,
    "apps": VK_APPS,
    "play_pause": VK_MEDIA_PLAY_PAUSE,
    "playpause": VK_MEDIA_PLAY_PAUSE,
    "next_track": VK_MEDIA_NEXT_TRACK,
    "previous_track": VK_MEDIA_PREV_TRACK,
    "stop": VK_MEDIA_STOP,
    "mute": VK_VOLUME_MUTE,
    "volume_up": VK_VOLUME_UP,
    "volume_down": VK_VOLUME_DOWN,
}


for _i in range(1, 25):
    _NAME_TO_VK[f"f{_i}"] = 0x6F + _i


def parse_combo(combo: str) -> list[int]:
    parts = [p.strip().lower() for p in combo.split("+") if p.strip()]
    vks: list[int] = []
    for part in parts:
        vk = _name_to_vk(part)
        if vk is None:
            raise ValueError(f"Unknown key name: {part!r}")
        vks.append(vk)
    return vks


def _name_to_vk(name: str) -> int | None:
    if name in _NAME_TO_VK:
        return _NAME_TO_VK[name]
    if len(name) == 1:
        ch = name.upper()
        if "A" <= ch <= "Z":
            return ord(ch)
        if "0" <= ch <= "9":
            return ord(ch)
    return None
