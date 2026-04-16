from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path

from .defaults import default_config
from .migrations import migrate
from .models import Config


log = logging.getLogger(__name__)


class ConfigStorage:
    def __init__(self, path: Path):
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> Config:
        if not self._path.exists():
            cfg = default_config()
            self.save(cfg)
            return cfg
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            log.warning("Cannot read config (%s); using defaults", exc)
            return default_config()
        try:
            migrated = migrate(raw)
            return Config.model_validate(migrated)
        except Exception as exc:
            log.warning("Config validation failed (%s); using defaults", exc)
            return default_config()

    def save(self, config: Config) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = config.model_dump(mode="json")
        text = json.dumps(payload, indent=2, ensure_ascii=False)
        directory = self._path.parent
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=directory,
            prefix=".config-",
            suffix=".tmp",
            delete=False,
        ) as tmp:
            tmp.write(text)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_path = Path(tmp.name)
        os.replace(tmp_path, self._path)
