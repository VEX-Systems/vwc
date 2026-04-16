from __future__ import annotations

from typing import Callable


class FakeTimerHandle:
    def __init__(self, clock: "FakeClock", callback: Callable[[], None]):
        self._clock = clock
        self._callback = callback
        self._fires_at: int | None = None

    def start(self, ms: int) -> None:
        self._fires_at = self._clock.now + ms
        self._clock._register(self)

    def stop(self) -> None:
        self._fires_at = None
        self._clock._unregister(self)

    def is_active(self) -> bool:
        return self._fires_at is not None

    @property
    def fires_at(self) -> int | None:
        return self._fires_at

    def _fire(self) -> None:
        self._fires_at = None
        self._callback()


class FakeClock:
    def __init__(self) -> None:
        self.now = 0
        self._timers: list[FakeTimerHandle] = []

    def create(self, callback: Callable[[], None]) -> FakeTimerHandle:
        return FakeTimerHandle(self, callback)

    def advance(self, ms: int) -> None:
        target = self.now + ms
        while True:
            due = [t for t in self._timers if t.fires_at is not None and t.fires_at <= target]
            if not due:
                break
            due.sort(key=lambda t: t.fires_at or 0)
            next_timer = due[0]
            self.now = next_timer.fires_at or self.now
            self._timers.remove(next_timer)
            next_timer._fire()
        self.now = target

    def _register(self, timer: FakeTimerHandle) -> None:
        if timer not in self._timers:
            self._timers.append(timer)

    def _unregister(self, timer: FakeTimerHandle) -> None:
        if timer in self._timers:
            self._timers.remove(timer)
