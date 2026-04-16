from __future__ import annotations

from enum import Enum


class Gesture(str, Enum):
    SINGLE_CLICK = "single_click"
    DOUBLE_CLICK = "double_click"
    TRIPLE_CLICK = "triple_click"
    QUADRUPLE_CLICK = "quadruple_click"
    QUINTUPLE_CLICK = "quintuple_click"
    SEXTUPLE_CLICK = "sextuple_click"
    SEPTUPLE_CLICK = "septuple_click"
    OCTUPLE_CLICK = "octuple_click"
    NONUPLE_CLICK = "nonuple_click"
    DECUPLE_CLICK = "decuple_click"
    LONG_PRESS = "long_press"
    ROTATE_UP = "rotate_up"
    ROTATE_DOWN = "rotate_down"
    HOLD_ROTATE_UP = "hold_rotate_up"
    HOLD_ROTATE_DOWN = "hold_rotate_down"


CLICK_GESTURES: tuple[Gesture, ...] = (
    Gesture.SINGLE_CLICK,
    Gesture.DOUBLE_CLICK,
    Gesture.TRIPLE_CLICK,
    Gesture.QUADRUPLE_CLICK,
    Gesture.QUINTUPLE_CLICK,
    Gesture.SEXTUPLE_CLICK,
    Gesture.SEPTUPLE_CLICK,
    Gesture.OCTUPLE_CLICK,
    Gesture.NONUPLE_CLICK,
    Gesture.DECUPLE_CLICK,
)


GESTURE_LABELS: dict[Gesture, str] = {
    Gesture.SINGLE_CLICK: "Single click",
    Gesture.DOUBLE_CLICK: "Double click",
    Gesture.TRIPLE_CLICK: "Triple click",
    Gesture.QUADRUPLE_CLICK: "4x click",
    Gesture.QUINTUPLE_CLICK: "5x click",
    Gesture.SEXTUPLE_CLICK: "6x click",
    Gesture.SEPTUPLE_CLICK: "7x click",
    Gesture.OCTUPLE_CLICK: "8x click",
    Gesture.NONUPLE_CLICK: "9x click",
    Gesture.DECUPLE_CLICK: "10x click",
    Gesture.LONG_PRESS: "Long press",
    Gesture.ROTATE_UP: "Rotate clockwise",
    Gesture.ROTATE_DOWN: "Rotate counter-clockwise",
    Gesture.HOLD_ROTATE_UP: "Click + rotate clockwise",
    Gesture.HOLD_ROTATE_DOWN: "Click + rotate counter-clockwise",
}


def click_gesture_for_count(n: int) -> Gesture:
    if n <= 0:
        return Gesture.SINGLE_CLICK
    if n > len(CLICK_GESTURES):
        return CLICK_GESTURES[-1]
    return CLICK_GESTURES[n - 1]
