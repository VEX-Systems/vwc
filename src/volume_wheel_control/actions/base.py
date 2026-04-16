from __future__ import annotations

from abc import ABC, abstractmethod


class Action(ABC):
    @abstractmethod
    def execute(self) -> None: ...

    def describe(self) -> str:
        return self.__class__.__name__
