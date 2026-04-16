from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from ..config.models import MatchRule


log = logging.getLogger(__name__)


@dataclass(frozen=True)
class WindowContext:
    process_name: str | None
    window_title: str | None


def matches(rule: MatchRule, context: WindowContext) -> bool:
    if rule.type == "process":
        if context.process_name is None:
            return False
        return rule.value.casefold() == context.process_name.casefold()
    if rule.type == "title_contains":
        if context.window_title is None:
            return False
        return rule.value.casefold() in context.window_title.casefold()
    if rule.type == "title_regex":
        if context.window_title is None:
            return False
        try:
            return re.search(rule.value, context.window_title) is not None
        except re.error as exc:
            log.warning("Invalid regex in match rule (%r): %s", rule.value, exc)
            return False
    return False
