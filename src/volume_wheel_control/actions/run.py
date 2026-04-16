from __future__ import annotations

import logging
import shlex
import subprocess
import sys
from pathlib import Path

from ..config.models import RunActionConfig
from .base import Action


log = logging.getLogger(__name__)


class RunAction(Action):
    def __init__(self, config: RunActionConfig):
        self._config = config

    def execute(self) -> None:
        path = self._config.path
        args = shlex.split(self._config.args) if self._config.args else []
        cwd = self._config.cwd or None
        flags = 0
        if sys.platform == "win32":
            flags = 0x00000008  # DETACHED_PROCESS
        try:
            subprocess.Popen(
                [path, *args],
                cwd=cwd,
                creationflags=flags,
                close_fds=True,
            )
        except (OSError, ValueError) as exc:
            log.warning("Cannot launch %s: %s", path, exc)

    def describe(self) -> str:
        name = Path(self._config.path).name or self._config.path
        return f"Run: {name}"
