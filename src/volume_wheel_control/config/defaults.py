from __future__ import annotations

from .models import (
    Config,
    GlobalProfile,
    MediaActionConfig,
    NoOpActionConfig,
    Settings,
)


def default_bindings() -> dict[str, object]:
    return {
        "single_click": MediaActionConfig(key="mute"),
        "double_click": MediaActionConfig(key="next_track"),
        "triple_click": MediaActionConfig(key="previous_track"),
        "quadruple_click": NoOpActionConfig(),
        "quintuple_click": NoOpActionConfig(),
        "sextuple_click": NoOpActionConfig(),
        "septuple_click": NoOpActionConfig(),
        "octuple_click": NoOpActionConfig(),
        "nonuple_click": NoOpActionConfig(),
        "decuple_click": NoOpActionConfig(),
        "long_press": MediaActionConfig(key="play_pause"),
        "rotate_up": MediaActionConfig(key="volume_up"),
        "rotate_down": MediaActionConfig(key="volume_down"),
        "hold_rotate_up": NoOpActionConfig(),
        "hold_rotate_down": NoOpActionConfig(),
    }


def default_config() -> Config:
    return Config(
        version=2,
        settings=Settings(),
        global_profile=GlobalProfile(bindings=default_bindings()),
        app_overrides=[],
    )
