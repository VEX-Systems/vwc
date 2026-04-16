from __future__ import annotations

import os
from pathlib import Path


APP_FOLDER_NAME = "VolumeWheelControl"


def appdata_root() -> Path:
    base = os.environ.get("APPDATA")
    if base:
        return Path(base) / APP_FOLDER_NAME
    return Path.home() / "AppData" / "Roaming" / APP_FOLDER_NAME


def config_path() -> Path:
    return appdata_root() / "config.json"


def logs_dir() -> Path:
    return appdata_root() / "logs"


def ensure_dirs() -> None:
    appdata_root().mkdir(parents=True, exist_ok=True)
    logs_dir().mkdir(parents=True, exist_ok=True)
