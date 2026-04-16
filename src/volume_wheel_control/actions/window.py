from __future__ import annotations

import logging

from ..config.models import WindowActionConfig
from ..input.keyboard_hook import send_key_combo
from ..input.keys import (
    VK_CONTROL,
    VK_LWIN,
    VK_MENU,
    VK_SHIFT,
    VK_TAB,
    parse_combo,
)
from ..windows import window_actions
from .base import Action


log = logging.getLogger(__name__)


_LABELS: dict[str, str] = {
    "minimize": "Minimize window",
    "maximize": "Maximize window",
    "restore": "Restore window",
    "close": "Close window",
    "minimize_all": "Show desktop",
    "switch_next": "Switch next window",
    "switch_prev": "Switch previous window",
    "fullscreen": "Toggle fullscreen",
}


class WindowAction(Action):
    def __init__(self, config: WindowActionConfig):
        self._config = config

    def execute(self) -> None:
        action = self._config.action
        if action == "minimize":
            window_actions.minimize_foreground()
        elif action == "maximize":
            window_actions.maximize_foreground()
        elif action == "restore":
            window_actions.restore_foreground()
        elif action == "close":
            window_actions.close_foreground()
        elif action == "minimize_all":
            send_key_combo([VK_LWIN, 0x44])
        elif action == "switch_next":
            send_key_combo([VK_MENU, VK_TAB])
        elif action == "switch_prev":
            send_key_combo([VK_MENU, VK_SHIFT, VK_TAB])
        elif action == "fullscreen":
            send_key_combo(parse_combo("f11"))
        else:
            log.warning("Unknown window action: %s", action)

    def describe(self) -> str:
        return _LABELS.get(self._config.action, self._config.action)
