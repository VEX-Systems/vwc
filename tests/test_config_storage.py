from __future__ import annotations

import json
from pathlib import Path

from volume_wheel_control.config.defaults import default_config
from volume_wheel_control.config.models import (
    AppOverride,
    HotkeyActionConfig,
    MatchRule,
)
from volume_wheel_control.config.storage import ConfigStorage


def test_load_creates_default_when_missing(tmp_path: Path):
    storage = ConfigStorage(tmp_path / "config.json")
    cfg = storage.load()
    assert cfg.version == 2
    assert (tmp_path / "config.json").exists()


def test_save_then_load_roundtrip(tmp_path: Path):
    storage = ConfigStorage(tmp_path / "config.json")
    cfg = default_config()
    cfg.app_overrides.append(
        AppOverride(
            name="Spotify",
            match=MatchRule(type="process", value="Spotify.exe"),
            bindings={"double_click": HotkeyActionConfig(keys="ctrl+right")},
        )
    )
    storage.save(cfg)
    loaded = storage.load()
    assert len(loaded.app_overrides) == 1
    assert loaded.app_overrides[0].name == "Spotify"


def test_corrupt_file_falls_back_to_default(tmp_path: Path):
    path = tmp_path / "config.json"
    path.write_text("{not json", encoding="utf-8")
    storage = ConfigStorage(path)
    cfg = storage.load()
    assert cfg.version == 2


def test_save_writes_atomically(tmp_path: Path):
    storage = ConfigStorage(tmp_path / "config.json")
    storage.save(default_config())
    assert (tmp_path / "config.json").exists()
    leftovers = list(tmp_path.glob(".config-*.tmp"))
    assert leftovers == []


def test_unknown_version_is_migrated(tmp_path: Path):
    path = tmp_path / "config.json"
    raw = {
        "version": 0,
        "global_profile": {
            "single_click": {"type": "media", "key": "mute"},
            "double_click": {"type": "media", "key": "next_track"},
            "triple_click": {"type": "media", "key": "previous_track"},
            "long_press": {"type": "media", "key": "play_pause"},
            "rotate_up": {"type": "media", "key": "volume_up"},
            "rotate_down": {"type": "media", "key": "volume_down"},
        },
    }
    path.write_text(json.dumps(raw), encoding="utf-8")
    storage = ConfigStorage(path)
    cfg = storage.load()
    assert cfg.version == 2
    assert "single_click" in cfg.global_profile.bindings
    assert cfg.global_profile.bindings["single_click"].type == "media"


def test_v1_flat_profile_migrates_to_dict(tmp_path: Path):
    path = tmp_path / "config.json"
    raw = {
        "version": 1,
        "settings": {},
        "global_profile": {
            "single_click": {"type": "media", "key": "mute"},
            "double_click": {"type": "window", "action": "fullscreen"},
            "triple_click": {"type": "media", "key": "previous_track"},
            "long_press": {"type": "media", "key": "play_pause"},
            "rotate_up": {"type": "media", "key": "volume_up"},
            "rotate_down": {"type": "media", "key": "volume_down"},
        },
    }
    path.write_text(json.dumps(raw), encoding="utf-8")
    storage = ConfigStorage(path)
    cfg = storage.load()
    assert cfg.version == 2
    assert cfg.global_profile.bindings["single_click"].type == "media"
    assert cfg.global_profile.bindings["double_click"].type == "window"
