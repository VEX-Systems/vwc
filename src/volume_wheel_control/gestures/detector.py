from __future__ import annotations

import logging
from enum import Enum
from typing import Callable

from ..input.raw_events import EventType, RawKey
from .gestures import Gesture, click_gesture_for_count
from .timer import TimerFactory, TimerHandle


log = logging.getLogger(__name__)


class _State(Enum):
    IDLE = "idle"
    PRESSED = "pressed"
    WAIT = "wait"
    LONG = "long"


class GestureDetector:
    def __init__(
        self,
        emit: Callable[[Gesture], None],
        timer_factory: TimerFactory,
        double_click_timeout_ms: int = 250,
        long_press_threshold_ms: int = 500,
        hold_rotate_window_ms: int = 600,
    ):
        self._emit = emit
        self._double_ms = double_click_timeout_ms
        self._long_ms = long_press_threshold_ms
        self._hold_rotate_ms = hold_rotate_window_ms
        self._state: _State = _State.IDLE
        self._is_down = False
        self._click_count = 0
        self._hold_rotate_armed_until: int = 0
        self._hold_rotate_consumed = False
        self._click_timer: TimerHandle = timer_factory.create(self._on_click_timeout)
        self._long_timer: TimerHandle = timer_factory.create(self._on_long_timeout)
        self._hold_rotate_timer: TimerHandle = timer_factory.create(self._on_hold_rotate_expired)

    def set_timings(
        self,
        double_click_timeout_ms: int,
        long_press_threshold_ms: int,
        hold_rotate_window_ms: int = 600,
    ) -> None:
        self._double_ms = double_click_timeout_ms
        self._long_ms = long_press_threshold_ms
        self._hold_rotate_ms = hold_rotate_window_ms

    def handle(self, key: RawKey, event: EventType) -> None:
        if key is RawKey.VOLUME_UP and event is EventType.DOWN:
            if self._hold_rotate_timer.is_active():
                self._cancel_pending_clicks()
                self._hold_rotate_consumed = True
                self._hold_rotate_timer.stop()
                self._emit(Gesture.HOLD_ROTATE_UP)
                return
            self._emit(Gesture.ROTATE_UP)
            return
        if key is RawKey.VOLUME_DOWN and event is EventType.DOWN:
            if self._hold_rotate_timer.is_active():
                self._cancel_pending_clicks()
                self._hold_rotate_consumed = True
                self._hold_rotate_timer.stop()
                self._emit(Gesture.HOLD_ROTATE_DOWN)
                return
            self._emit(Gesture.ROTATE_DOWN)
            return
        if key is not RawKey.MUTE:
            return

        if event is EventType.DOWN:
            self._on_down()
        elif event is EventType.UP:
            self._on_up()

    def _on_down(self) -> None:
        if self._is_down:
            return
        self._is_down = True

        if self._state is _State.IDLE:
            self._state = _State.PRESSED
            self._click_count = 1
            self._hold_rotate_consumed = False
            self._long_timer.start(self._long_ms)
        elif self._state is _State.WAIT:
            self._click_timer.stop()
            self._hold_rotate_timer.stop()
            self._state = _State.PRESSED
            self._click_count += 1
            self._long_timer.start(self._long_ms)

    def _on_up(self) -> None:
        if not self._is_down:
            return
        self._is_down = False

        if self._state is _State.LONG:
            self._reset()
            return
        if self._state is _State.PRESSED:
            self._long_timer.stop()
            self._state = _State.WAIT
            self._click_timer.start(self._double_ms)
            self._hold_rotate_timer.start(self._hold_rotate_ms)

    def _on_click_timeout(self) -> None:
        if self._state is not _State.WAIT:
            return
        if self._hold_rotate_consumed:
            return
        count = self._click_count
        gesture = click_gesture_for_count(count)
        self._click_count = 0
        self._state = _State.IDLE
        self._emit(gesture)

    def _on_long_timeout(self) -> None:
        if self._state is not _State.PRESSED:
            return
        self._state = _State.LONG
        self._click_count = 0
        self._hold_rotate_timer.stop()
        self._emit(Gesture.LONG_PRESS)

    def _on_hold_rotate_expired(self) -> None:
        pass

    def _cancel_pending_clicks(self) -> None:
        self._click_timer.stop()
        self._click_count = 0
        self._state = _State.IDLE

    def _reset(self) -> None:
        self._click_count = 0
        self._click_timer.stop()
        self._long_timer.stop()
        self._hold_rotate_timer.stop()
        self._hold_rotate_consumed = False
        self._state = _State.IDLE
