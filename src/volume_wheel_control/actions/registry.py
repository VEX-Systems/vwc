from __future__ import annotations

from ..config.models import (
    ActionConfig,
    HotkeyActionConfig,
    MediaActionConfig,
    NoOpActionConfig,
    RunActionConfig,
    WindowActionConfig,
)
from .base import Action
from .hotkey import HotkeyAction
from .media import MediaAction
from .noop import NoOpAction
from .run import RunAction
from .window import WindowAction


def build_action(config: ActionConfig) -> Action:
    if isinstance(config, MediaActionConfig):
        return MediaAction(config)
    if isinstance(config, HotkeyActionConfig):
        return HotkeyAction(config)
    if isinstance(config, RunActionConfig):
        return RunAction(config)
    if isinstance(config, WindowActionConfig):
        return WindowAction(config)
    if isinstance(config, NoOpActionConfig):
        return NoOpAction(config)
    raise TypeError(f"Unknown action config type: {type(config).__name__}")
