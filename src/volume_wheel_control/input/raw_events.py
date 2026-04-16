from __future__ import annotations

from enum import Enum


class RawKey(str, Enum):
    MUTE = "mute"
    VOLUME_UP = "volume_up"
    VOLUME_DOWN = "volume_down"


class EventType(str, Enum):
    DOWN = "down"
    UP = "up"
