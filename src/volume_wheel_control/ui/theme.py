from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QIcon, QLinearGradient, QPainter, QPen, QPixmap, QSurfaceFormat
from qfluentwidgets import Theme, setTheme, setThemeColor


ACCENT = "#7A5CFF"


def apply_theme() -> None:
    setTheme(Theme.DARK)
    setThemeColor(ACCENT)


def configure_surface_for_smoothness() -> None:
    fmt = QSurfaceFormat.defaultFormat()
    fmt.setSwapInterval(1)
    fmt.setSamples(0)
    fmt.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)
    QSurfaceFormat.setDefaultFormat(fmt)


def disable_animations(qt_app) -> None:
    from PyQt6.QtCore import Qt as _Qt
    for effect in (
        _Qt.UIEffect.UI_AnimateMenu,
        _Qt.UIEffect.UI_AnimateCombo,
        _Qt.UIEffect.UI_AnimateTooltip,
        _Qt.UIEffect.UI_AnimateToolBox,
        _Qt.UIEffect.UI_FadeMenu,
        _Qt.UIEffect.UI_FadeTooltip,
    ):
        try:
            qt_app.setEffectEnabled(effect, False)
        except Exception:
            pass


def app_icon() -> QIcon:
    return QIcon(_render_knob_pixmap(64, active=True))


def tray_icon(active: bool) -> QIcon:
    return QIcon(_render_knob_pixmap(32, active=active))


def _render_knob_pixmap(size: int, active: bool) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    bg_rect = QRectF(1, 1, size - 2, size - 2)
    gradient = QLinearGradient(0, 0, 0, size)
    if active:
        gradient.setColorAt(0.0, QColor(140, 110, 255))
        gradient.setColorAt(1.0, QColor(90, 60, 200))
    else:
        gradient.setColorAt(0.0, QColor(120, 120, 130))
        gradient.setColorAt(1.0, QColor(70, 70, 80))
    painter.setBrush(QBrush(gradient))
    painter.setPen(QPen(QColor(30, 30, 40), 1.5))
    painter.drawEllipse(bg_rect)

    inset = size * 0.28
    inner = QRectF(inset, inset, size - inset * 2, size - inset * 2)
    inner_grad = QLinearGradient(0, inner.top(), 0, inner.bottom())
    inner_grad.setColorAt(0.0, QColor(40, 40, 55))
    inner_grad.setColorAt(1.0, QColor(20, 20, 30))
    painter.setBrush(QBrush(inner_grad))
    painter.setPen(QPen(QColor(10, 10, 15), 1))
    painter.drawEllipse(inner)

    tick_color = QColor(245, 245, 255) if active else QColor(160, 160, 170)
    painter.setPen(QPen(tick_color, max(1.5, size * 0.04)))
    cx = size / 2
    cy = size / 2
    r_outer = size / 2 - 2
    r_inner = size * 0.32
    painter.drawLine(int(cx), int(cy - r_outer * 0.78), int(cx), int(cy - r_inner))

    painter.end()
    return pixmap
