from __future__ import annotations

from ..config.models import NoOpActionConfig
from .base import Action


class NoOpAction(Action):
    def __init__(self, config: NoOpActionConfig):
        self._config = config

    def execute(self) -> None:
        return

    def describe(self) -> str:
        return "Disabled"
