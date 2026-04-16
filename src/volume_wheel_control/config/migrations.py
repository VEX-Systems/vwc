from __future__ import annotations

from typing import Any, Callable


CURRENT_VERSION = 2


def migrate(raw: dict[str, Any]) -> dict[str, Any]:
    version = int(raw.get("version", 0))
    while version < CURRENT_VERSION:
        step = _MIGRATIONS.get(version)
        if step is None:
            break
        raw = step(raw)
        version = int(raw.get("version", version + 1))
    return raw


def _v0_to_v1(raw: dict[str, Any]) -> dict[str, Any]:
    raw["version"] = 1
    raw.setdefault("settings", {})
    raw.setdefault("app_overrides", [])
    return raw


def _v1_to_v2(raw: dict[str, Any]) -> dict[str, Any]:
    raw["version"] = 2
    profile = raw.get("global_profile") or {}
    if "bindings" in profile and isinstance(profile["bindings"], dict):
        return raw
    flat_keys = (
        "single_click",
        "double_click",
        "triple_click",
        "long_press",
        "rotate_up",
        "rotate_down",
    )
    bindings: dict[str, Any] = {}
    for key in flat_keys:
        if key in profile:
            bindings[key] = profile[key]
    raw["global_profile"] = {"bindings": bindings}
    return raw


_MIGRATIONS: dict[int, Callable[[dict[str, Any]], dict[str, Any]]] = {
    0: _v0_to_v1,
    1: _v1_to_v2,
}
