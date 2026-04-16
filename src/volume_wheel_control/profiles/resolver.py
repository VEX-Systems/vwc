from __future__ import annotations

from ..config.models import ActionConfig, Config
from ..gestures.gestures import Gesture
from .matchers import WindowContext, matches


def resolve(gesture: Gesture, context: WindowContext, config: Config) -> ActionConfig:
    gesture_name = gesture.value
    for override in config.app_overrides:
        if matches(override.match, context):
            if gesture_name in override.bindings:
                return override.bindings[gesture_name]
            return config.global_profile.get(gesture_name)
    return config.global_profile.get(gesture_name)
