from __future__ import annotations

from volume_wheel_control.gestures.detector import GestureDetector
from volume_wheel_control.gestures.gestures import Gesture
from volume_wheel_control.input.raw_events import EventType, RawKey

from .fakes import FakeClock


def _make_detector(clock: FakeClock, dbl: int = 250, long: int = 500, hold: int = 600):
    emitted: list[Gesture] = []
    detector = GestureDetector(
        emit=emitted.append,
        timer_factory=clock,
        double_click_timeout_ms=dbl,
        long_press_threshold_ms=long,
        hold_rotate_window_ms=hold,
    )
    return detector, emitted


def _click(detector: GestureDetector, clock: FakeClock, hold_ms: int = 20, rest_ms: int = 40):
    detector.handle(RawKey.MUTE, EventType.DOWN)
    clock.advance(hold_ms)
    detector.handle(RawKey.MUTE, EventType.UP)
    clock.advance(rest_ms)


def test_rotate_up_emits_immediately():
    clock = FakeClock()
    detector, emitted = _make_detector(clock)
    detector.handle(RawKey.VOLUME_UP, EventType.DOWN)
    assert emitted == [Gesture.ROTATE_UP]


def test_rotate_down_emits_immediately():
    clock = FakeClock()
    detector, emitted = _make_detector(clock)
    detector.handle(RawKey.VOLUME_DOWN, EventType.DOWN)
    assert emitted == [Gesture.ROTATE_DOWN]


def test_single_click_emits_after_timeout():
    clock = FakeClock()
    detector, emitted = _make_detector(clock, dbl=250)
    _click(detector, clock)
    assert emitted == []
    clock.advance(260)
    assert emitted == [Gesture.SINGLE_CLICK]


def test_double_click_emits_after_timeout():
    clock = FakeClock()
    detector, emitted = _make_detector(clock, dbl=250)
    _click(detector, clock, rest_ms=100)
    _click(detector, clock, rest_ms=0)
    clock.advance(260)
    assert emitted == [Gesture.DOUBLE_CLICK]


def test_triple_click_emits_after_timeout():
    clock = FakeClock()
    detector, emitted = _make_detector(clock, dbl=250)
    _click(detector, clock, rest_ms=80)
    _click(detector, clock, rest_ms=80)
    _click(detector, clock, rest_ms=0)
    clock.advance(260)
    assert emitted == [Gesture.TRIPLE_CLICK]


def test_quadruple_click():
    clock = FakeClock()
    detector, emitted = _make_detector(clock, dbl=250)
    for _ in range(4):
        _click(detector, clock, rest_ms=80)
    clock.advance(260)
    assert emitted == [Gesture.QUADRUPLE_CLICK]


def test_quintuple_click():
    clock = FakeClock()
    detector, emitted = _make_detector(clock, dbl=250)
    for _ in range(5):
        _click(detector, clock, rest_ms=80)
    clock.advance(260)
    assert emitted == [Gesture.QUINTUPLE_CLICK]


def test_eleven_clicks_cap_at_decuple():
    clock = FakeClock()
    detector, emitted = _make_detector(clock, dbl=250)
    for _ in range(11):
        _click(detector, clock, rest_ms=80)
    clock.advance(260)
    assert emitted == [Gesture.DECUPLE_CLICK]


def test_hold_rotate_up_after_click():
    clock = FakeClock()
    detector, emitted = _make_detector(clock, dbl=250)
    _click(detector, clock, rest_ms=100)
    detector.handle(RawKey.VOLUME_UP, EventType.DOWN)
    assert emitted == [Gesture.HOLD_ROTATE_UP]
    clock.advance(500)
    assert emitted == [Gesture.HOLD_ROTATE_UP]


def test_hold_rotate_down_after_click():
    clock = FakeClock()
    detector, emitted = _make_detector(clock, dbl=250)
    _click(detector, clock, rest_ms=50)
    detector.handle(RawKey.VOLUME_DOWN, EventType.DOWN)
    assert emitted == [Gesture.HOLD_ROTATE_DOWN]


def test_rotation_outside_hold_window_is_plain_rotate():
    clock = FakeClock()
    detector, emitted = _make_detector(clock, dbl=250)
    _click(detector, clock, rest_ms=0)
    clock.advance(260)
    assert emitted == [Gesture.SINGLE_CLICK]
    clock.advance(500)
    detector.handle(RawKey.VOLUME_UP, EventType.DOWN)
    assert emitted == [Gesture.SINGLE_CLICK, Gesture.ROTATE_UP]


def test_long_press_emits_after_threshold():
    clock = FakeClock()
    detector, emitted = _make_detector(clock, long=500)
    detector.handle(RawKey.MUTE, EventType.DOWN)
    clock.advance(500)
    assert emitted == [Gesture.LONG_PRESS]
    detector.handle(RawKey.MUTE, EventType.UP)
    clock.advance(400)
    assert emitted == [Gesture.LONG_PRESS]


def test_key_repeat_ignored():
    clock = FakeClock()
    detector, emitted = _make_detector(clock, dbl=250)
    detector.handle(RawKey.MUTE, EventType.DOWN)
    detector.handle(RawKey.MUTE, EventType.DOWN)
    detector.handle(RawKey.MUTE, EventType.DOWN)
    clock.advance(50)
    detector.handle(RawKey.MUTE, EventType.UP)
    clock.advance(260)
    assert emitted == [Gesture.SINGLE_CLICK]


def test_release_before_long_threshold_does_not_emit_long_press():
    clock = FakeClock()
    detector, emitted = _make_detector(clock, dbl=250, long=500)
    detector.handle(RawKey.MUTE, EventType.DOWN)
    clock.advance(300)
    detector.handle(RawKey.MUTE, EventType.UP)
    clock.advance(260)
    assert emitted == [Gesture.SINGLE_CLICK]


def test_set_timings_updates_thresholds():
    clock = FakeClock()
    detector, emitted = _make_detector(clock, dbl=250)
    detector.set_timings(double_click_timeout_ms=100, long_press_threshold_ms=500)
    _click(detector, clock, rest_ms=0)
    clock.advance(120)
    assert emitted == [Gesture.SINGLE_CLICK]
