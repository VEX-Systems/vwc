from __future__ import annotations

from volume_wheel_control.config.defaults import default_config
from volume_wheel_control.config.models import (
    AppOverride,
    HotkeyActionConfig,
    MatchRule,
    MediaActionConfig,
    NoOpActionConfig,
)
from volume_wheel_control.gestures.gestures import Gesture
from volume_wheel_control.profiles.matchers import WindowContext
from volume_wheel_control.profiles.resolver import resolve


def test_resolve_falls_back_to_global_when_no_overrides():
    cfg = default_config()
    ctx = WindowContext(process_name="anything.exe", window_title="x")
    result = resolve(Gesture.DOUBLE_CLICK, ctx, cfg)
    assert isinstance(result, MediaActionConfig)
    assert result.key == "next_track"


def test_resolve_uses_override_when_process_matches():
    cfg = default_config()
    cfg.app_overrides.append(
        AppOverride(
            name="Spotify",
            match=MatchRule(type="process", value="Spotify.exe"),
            bindings={"double_click": HotkeyActionConfig(keys="ctrl+right")},
        )
    )
    ctx = WindowContext(process_name="Spotify.exe", window_title="Song")
    result = resolve(Gesture.DOUBLE_CLICK, ctx, cfg)
    assert isinstance(result, HotkeyActionConfig)
    assert result.keys == "ctrl+right"


def test_override_matches_case_insensitively():
    cfg = default_config()
    cfg.app_overrides.append(
        AppOverride(
            name="Spotify",
            match=MatchRule(type="process", value="spotify.exe"),
            bindings={"double_click": HotkeyActionConfig(keys="ctrl+right")},
        )
    )
    ctx = WindowContext(process_name="SPOTIFY.EXE", window_title="")
    result = resolve(Gesture.DOUBLE_CLICK, ctx, cfg)
    assert isinstance(result, HotkeyActionConfig)


def test_override_falls_back_to_global_for_unbound_gesture():
    cfg = default_config()
    cfg.app_overrides.append(
        AppOverride(
            name="Spotify",
            match=MatchRule(type="process", value="Spotify.exe"),
            bindings={"double_click": HotkeyActionConfig(keys="ctrl+right")},
        )
    )
    ctx = WindowContext(process_name="Spotify.exe", window_title="")
    result = resolve(Gesture.SINGLE_CLICK, ctx, cfg)
    assert isinstance(result, MediaActionConfig)
    assert result.key == "mute"


def test_first_matching_override_wins():
    cfg = default_config()
    cfg.app_overrides.append(
        AppOverride(
            name="First",
            match=MatchRule(type="process", value="App.exe"),
            bindings={"double_click": HotkeyActionConfig(keys="alt+1")},
        )
    )
    cfg.app_overrides.append(
        AppOverride(
            name="Second",
            match=MatchRule(type="process", value="App.exe"),
            bindings={"double_click": HotkeyActionConfig(keys="alt+2")},
        )
    )
    ctx = WindowContext(process_name="App.exe", window_title="")
    result = resolve(Gesture.DOUBLE_CLICK, ctx, cfg)
    assert isinstance(result, HotkeyActionConfig)
    assert result.keys == "alt+1"


def test_title_contains_match():
    cfg = default_config()
    cfg.app_overrides.append(
        AppOverride(
            name="YouTube",
            match=MatchRule(type="title_contains", value="YouTube"),
            bindings={"long_press": HotkeyActionConfig(keys="space")},
        )
    )
    ctx = WindowContext(process_name="chrome.exe", window_title="Cool Video - YouTube - Chrome")
    result = resolve(Gesture.LONG_PRESS, ctx, cfg)
    assert isinstance(result, HotkeyActionConfig)
    assert result.keys == "space"


def test_invalid_regex_does_not_crash():
    cfg = default_config()
    cfg.app_overrides.append(
        AppOverride(
            name="Bad",
            match=MatchRule(type="title_regex", value="(unclosed"),
            bindings={"single_click": HotkeyActionConfig(keys="esc")},
        )
    )
    ctx = WindowContext(process_name=None, window_title="anything")
    result = resolve(Gesture.SINGLE_CLICK, ctx, cfg)
    assert isinstance(result, MediaActionConfig)
