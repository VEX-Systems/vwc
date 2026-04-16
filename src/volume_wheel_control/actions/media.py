from __future__ import annotations

from ..config.models import MediaActionConfig
from ..input.keyboard_hook import (
    VK_VOLUME_DOWN,
    VK_VOLUME_MUTE,
    VK_VOLUME_UP,
    send_media_key,
)
from .base import Action


VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3


_VK_MAP: dict[str, int] = {
    "play_pause": VK_MEDIA_PLAY_PAUSE,
    "next_track": VK_MEDIA_NEXT_TRACK,
    "previous_track": VK_MEDIA_PREV_TRACK,
    "stop": VK_MEDIA_STOP,
    "mute": VK_VOLUME_MUTE,
    "volume_up": VK_VOLUME_UP,
    "volume_down": VK_VOLUME_DOWN,
}

_LABELS: dict[str, str] = {
    "play_pause": "Play / Pause",
    "next_track": "Next track",
    "previous_track": "Previous track",
    "stop": "Stop",
    "mute": "Mute",
    "volume_up": "Volume up",
    "volume_down": "Volume down",
}


class MediaAction(Action):
    def __init__(self, config: MediaActionConfig):
        self._config = config

    def execute(self) -> None:
        vk = _VK_MAP[self._config.key]
        send_media_key(vk)

    def describe(self) -> str:
        return _LABELS[self._config.key]
