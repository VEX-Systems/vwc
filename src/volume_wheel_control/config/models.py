from __future__ import annotations

from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field, field_validator


GESTURE_NAMES = (
    "single_click",
    "double_click",
    "triple_click",
    "quadruple_click",
    "quintuple_click",
    "sextuple_click",
    "septuple_click",
    "octuple_click",
    "nonuple_click",
    "decuple_click",
    "long_press",
    "rotate_up",
    "rotate_down",
    "hold_rotate_up",
    "hold_rotate_down",
)

GestureName = Literal[
    "single_click",
    "double_click",
    "triple_click",
    "quadruple_click",
    "quintuple_click",
    "sextuple_click",
    "septuple_click",
    "octuple_click",
    "nonuple_click",
    "decuple_click",
    "long_press",
    "rotate_up",
    "rotate_down",
    "hold_rotate_up",
    "hold_rotate_down",
]

MediaKey = Literal[
    "play_pause",
    "next_track",
    "previous_track",
    "stop",
    "mute",
    "volume_up",
    "volume_down",
]

WindowAction = Literal[
    "minimize",
    "maximize",
    "restore",
    "close",
    "minimize_all",
    "switch_next",
    "switch_prev",
    "fullscreen",
]

MatchType = Literal["process", "title_contains", "title_regex"]


class MediaActionConfig(BaseModel):
    type: Literal["media"] = "media"
    key: MediaKey


class HotkeyActionConfig(BaseModel):
    type: Literal["hotkey"] = "hotkey"
    keys: str

    @field_validator("keys")
    @classmethod
    def _strip_keys(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("hotkey 'keys' cannot be empty")
        return cleaned


class RunActionConfig(BaseModel):
    type: Literal["run"] = "run"
    path: str
    args: str = ""
    cwd: str = ""

    @field_validator("path")
    @classmethod
    def _strip_path(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("run 'path' cannot be empty")
        return cleaned


class WindowActionConfig(BaseModel):
    type: Literal["window"] = "window"
    action: WindowAction


class NoOpActionConfig(BaseModel):
    type: Literal["none"] = "none"


ActionConfig = Annotated[
    Union[
        MediaActionConfig,
        HotkeyActionConfig,
        RunActionConfig,
        WindowActionConfig,
        NoOpActionConfig,
    ],
    Field(discriminator="type"),
]


class MatchRule(BaseModel):
    type: MatchType
    value: str


class GlobalProfile(BaseModel):
    bindings: dict[str, ActionConfig] = Field(default_factory=dict)

    @field_validator("bindings")
    @classmethod
    def _validate_keys(cls, value: dict[str, Any]) -> dict[str, Any]:
        for key in value:
            if key not in GESTURE_NAMES:
                raise ValueError(f"Unknown gesture in global profile bindings: {key}")
        return value

    def get(self, gesture: str) -> ActionConfig:
        if gesture in self.bindings:
            return self.bindings[gesture]
        return NoOpActionConfig()

    def set(self, gesture: str, action: ActionConfig) -> None:
        self.bindings[gesture] = action


class AppOverride(BaseModel):
    name: str
    match: MatchRule
    bindings: dict[GestureName, ActionConfig] = Field(default_factory=dict)

    @field_validator("bindings")
    @classmethod
    def _validate_keys(cls, value: dict[str, Any]) -> dict[str, Any]:
        for key in value:
            if key not in GESTURE_NAMES:
                raise ValueError(f"Unknown gesture in override bindings: {key}")
        return value


class Settings(BaseModel):
    double_click_timeout_ms: int = Field(default=250, ge=50, le=2000)
    long_press_threshold_ms: int = Field(default=500, ge=200, le=3000)
    hold_rotate_window_ms: int = Field(default=600, ge=200, le=2000)
    start_with_windows: bool = True
    suppress_default_actions: bool = True
    paused: bool = False
    show_gesture_hint: bool = False


class Config(BaseModel):
    version: int = 2
    settings: Settings = Field(default_factory=Settings)
    global_profile: GlobalProfile
    app_overrides: list[AppOverride] = Field(default_factory=list)
