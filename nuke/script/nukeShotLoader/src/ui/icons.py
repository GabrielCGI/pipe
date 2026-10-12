"""Programmatic icons (no image assets; predictable across Qt versions).

Icon factories are cached: rows repaint their buttons on every refresh.
"""

import contextlib
import functools
import math
import os

from .qt import QtCore, QtGui

_DARK = "#1e1e1e"


@contextlib.contextmanager
def _painter(pixmap, pen_color=None, width=1.3):
    painter = QtGui.QPainter(pixmap)
    try:
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        if pen_color:
            pen = QtGui.QPen(QtGui.QColor(pen_color))
            pen.setWidthF(width)
            pen.setCapStyle(QtCore.Qt.RoundCap)
            pen.setJoinStyle(QtCore.Qt.RoundJoin)
            painter.setPen(pen)
        yield painter
    finally:
        painter.end()


def _canvas(size):
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(QtCore.Qt.transparent)
    return pixmap


@functools.lru_cache(maxsize=None)
def trash_icon(color="#c8a0a0", size=16):
    pixmap = _canvas(size)
    with _painter(pixmap, color, 1.3) as p:
        for line in ((6, 3, 10, 3), (6, 3, 6, 5), (10, 3, 10, 5),   # handle
                     (3, 5, 13, 5),                                   # lid
                     (4, 6, 5, 13), (12, 6, 11, 13), (5, 13, 11, 13),  # body
                     (7, 7, 7, 12), (9, 7, 9, 12)):                   # ribs
            p.drawLine(*line)
    return QtGui.QIcon(pixmap)


@functools.lru_cache(maxsize=None)
def recover_icon(color="#8ac68a", size=16):
    """↩-style arrow: 'put this back'."""
    pixmap = _canvas(size)
    with _painter(pixmap, color, 1.4) as p:
        for line in ((12, 3, 12, 10), (12, 10, 4, 10), (4, 10, 7, 7), (4, 10, 7, 13)):
            p.drawLine(*line)
    return QtGui.QIcon(pixmap)


@functools.lru_cache(maxsize=None)
def snowflake_icon(color="#8ac8e0", filled=False, size=16):
    """Six-branch snowflake; heavier stroke for the frozen state."""
    pixmap = _canvas(size)
    with _painter(pixmap, color, 1.6 if filled else 1.15) as p:
        c = size / 2.0
        arm = size / 2.0 - 1.5
        tick = arm * 0.45
        for i in range(6):
            a = i * math.pi / 3.0
            p.drawLine(QtCore.QPointF(c, c), QtCore.QPointF(c + arm * math.cos(a), c + arm * math.sin(a)))
            mx, my = c + arm * 0.55 * math.cos(a), c + arm * 0.55 * math.sin(a)
            for da in (math.pi / 4, -math.pi / 4):
                p.drawLine(QtCore.QPointF(mx, my),
                           QtCore.QPointF(mx + tick * math.cos(a + da), my + tick * math.sin(a + da)))
    return QtGui.QIcon(pixmap)


@functools.lru_cache(maxsize=None)
def warning_icon(color="#f5c542", size=16):
    pixmap = _canvas(size)
    with _painter(pixmap) as p:
        pad = 1.0
        p.setPen(QtGui.QPen(QtGui.QColor(_DARK), 1.0))
        p.setBrush(QtGui.QBrush(QtGui.QColor(color)))
        p.drawPolygon(QtGui.QPolygonF([
            QtCore.QPointF(size / 2.0, pad),
            QtCore.QPointF(size - pad, size - pad),
            QtCore.QPointF(pad, size - pad),
        ]))
        pen = QtGui.QPen(QtGui.QColor(_DARK))
        pen.setWidthF(1.6)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        p.setPen(pen)
        c = size / 2.0
        p.drawLine(QtCore.QPointF(c, size * 0.35), QtCore.QPointF(c, size * 0.65))
        p.setBrush(QtGui.QBrush(QtGui.QColor(_DARK)))
        p.setPen(QtCore.Qt.NoPen)
        dot = max(1.0, size * 0.07)
        p.drawEllipse(QtCore.QPointF(c, size * 0.78), dot, dot)
    return QtGui.QIcon(pixmap)


@functools.lru_cache(maxsize=None)
def pause_icon(color="#b7b7b7", size=12):
    pixmap = _canvas(size)
    with _painter(pixmap) as p:
        p.setPen(QtCore.Qt.NoPen)
        p.setBrush(QtGui.QBrush(QtGui.QColor(color)))
        bar_w, bar_h, gap = 2, 8, 2
        top = (size - bar_h) // 2
        left = (size - (bar_w * 2 + gap)) // 2
        p.drawRect(left, top, bar_w, bar_h)
        p.drawRect(left + bar_w + gap, top, bar_w, bar_h)
    return QtGui.QIcon(pixmap)


@functools.lru_cache(maxsize=None)
def play_icon(color="#b7b7b7", size=12):
    pixmap = _canvas(size)
    with _painter(pixmap) as p:
        p.setPen(QtCore.Qt.NoPen)
        p.setBrush(QtGui.QBrush(QtGui.QColor(color)))
        p.drawPolygon(QtGui.QPolygonF([
            QtCore.QPointF(3.0, 2.0),
            QtCore.QPointF(3.0, size - 2.0),
            QtCore.QPointF(size - 2.0, size / 2.0),
        ]))
    return QtGui.QIcon(pixmap)


@functools.lru_cache(maxsize=None)
def spinner_pixmap(angle, size=18, color="#b7b7b7"):
    """Two 140° arcs with arrow heads, rotated by `angle` degrees (the
    status bar steps through 120 angles, 10 times a second)."""
    pixmap = _canvas(size)
    qcolor = QtGui.QColor(color)
    with _painter(pixmap) as p:
        p.translate(size / 2.0, size / 2.0)
        p.rotate(angle)
        pen = QtGui.QPen(qcolor)
        pen.setWidth(2)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        p.setPen(pen)
        r = size / 2.0 - 3.0
        rect = QtCore.QRectF(-r, -r, 2 * r, 2 * r)
        p.drawArc(rect, 40 * 16, 140 * 16)   # Qt arcs are in 1/16°
        p.drawArc(rect, 220 * 16, 140 * 16)
        p.setPen(QtCore.Qt.NoPen)
        p.setBrush(QtGui.QBrush(qcolor))
        for start in (40.0, 220.0):
            rad = math.radians(start)
            tx, ty = r * math.cos(rad), -r * math.sin(rad)
            tangent = math.radians(start + 90.0)
            nx, ny = math.cos(tangent), -math.sin(tangent)
            rx, ry = math.cos(rad), -math.sin(rad)
            p.drawPolygon(QtGui.QPolygonF([
                QtCore.QPointF(tx + nx * 3.5, ty + ny * 3.5),
                QtCore.QPointF(tx + rx * 2.0, ty + ry * 2.0),
                QtCore.QPointF(tx - rx * 2.0, ty - ry * 2.0),
            ]))
    return pixmap


def _load_scaled(path, height):
    if not path or not os.path.exists(path):
        return None
    source = QtGui.QPixmap(path)
    if source.isNull():
        return None
    return source.scaledToHeight(height, QtCore.Qt.SmoothTransformation)


def rounded_pixmap(path, height, radius=6):
    """Image scaled to `height` with rounded corners, None if unreadable."""
    scaled = _load_scaled(path, height)
    if scaled is None:
        return None
    result = QtGui.QPixmap(scaled.size())
    result.fill(QtCore.Qt.transparent)
    with _painter(result) as p:
        clip = QtGui.QPainterPath()
        clip.addRoundedRect(QtCore.QRectF(0, 0, scaled.width(), scaled.height()), radius, radius)
        p.setClipPath(clip)
        p.drawPixmap(0, 0, scaled)
    return result


def faded_pixmap(path, height, opacity):
    """Image scaled to `height` with pre-multiplied `opacity`, None if unreadable."""
    scaled = _load_scaled(path, height)
    if scaled is None:
        print(f"[ShotAssetLoader] Logo not found or unreadable: {path}")
        return None
    result = QtGui.QPixmap(scaled.size())
    result.fill(QtCore.Qt.transparent)
    with _painter(result) as p:
        p.setOpacity(opacity)
        p.drawPixmap(0, 0, scaled)
    return result
