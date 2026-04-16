from __future__ import annotations

import logging

from ..config.models import HotkeyActionConfig
from ..input.keyboard_hook import send_key_combo
from ..input.keys import parse_combo
from .base import Action


log = logging.getLogger(__name__)


class HotkeyAction(Action):
    def __init__(self, config: HotkeyActionConfig):
        self._config = config

    def execute(self) -> None:
        try:
            vks = parse_combo(self._config.keys)
        except ValueError as exc:
            log.warning("Invalid hotkey %r: %s", self._config.keys, exc)
            return
        if not vks:
            return
        send_key_combo(vks)

    def describe(self) -> str:
        return f"Hotkey: {_pretty(self._config.keys)}"


def _pretty(keys: str) -> str:
    parts = [p.strip() for p in keys.split("+") if p.strip()]
    return " + ".join(p.capitalize() for p in parts)
