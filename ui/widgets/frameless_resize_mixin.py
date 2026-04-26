"""无边框模式边缘拖拽缩放 Mixin

使用方式:
    class MainWindow(FramelessResizeMixin, QMainWindow):
        def __init__(self):
            super().__init__()
            self.init_resize_state()
            ...
        def _apply_frameless_mode(self, enabled):
            ...
            self._set_resize_mouse_tracking(enabled)
            if enabled:
                QApplication.instance().installEventFilter(self)
            else:
                QApplication.instance().removeEventFilter(self)
                self._restore_override_cursor()
"""
from PyQt6.QtWidgets import QWidget, QFrame, QApplication
from PyQt6.QtCore import Qt, QEvent


class FramelessResizeMixin:
    """无边框窗口边缘拖拽缩放 — 纯 PyQt6 实现，避免 ctypes+nativeEvent 导致的 segfault"""

    _EDGE_MARGIN = 5

    def init_resize_state(self):
        self._resize_edge = None          # Qt.Edge | None
        self._resize_start_geo = None     # QRect
        self._resize_start_pos = None     # QPoint (global)
        self._override_cursor_active = False

    # ---- 鼠标追踪 ----

    def _set_resize_mouse_tracking(self, enabled):
        central = self.centralWidget()
        central.setMouseTracking(enabled)
        for w in central.findChildren(QFrame):
            w.setMouseTracking(enabled)

    # ---- 边缘检测 ----

    def _hit_edge(self, pos):
        m = self._EDGE_MARGIN
        r = self.rect()
        l = pos.x() < m
        ri = pos.x() > r.width() - m
        t = pos.y() < m
        b = pos.y() > r.height() - m
        if t and l:    return Qt.Edge.TopEdge | Qt.Edge.LeftEdge
        if t and ri:   return Qt.Edge.TopEdge | Qt.Edge.RightEdge
        if b and l:    return Qt.Edge.BottomEdge | Qt.Edge.LeftEdge
        if b and ri:   return Qt.Edge.BottomEdge | Qt.Edge.RightEdge
        if t:          return Qt.Edge.TopEdge
        if b:          return Qt.Edge.BottomEdge
        if l:          return Qt.Edge.LeftEdge
        if ri:         return Qt.Edge.RightEdge
        return None

    @staticmethod
    def _edge_cursor(edge):
        if edge == Qt.Edge.TopEdge or edge == Qt.Edge.BottomEdge:
            return Qt.CursorShape.SizeVerCursor
        if edge == Qt.Edge.LeftEdge or edge == Qt.Edge.RightEdge:
            return Qt.CursorShape.SizeHorCursor
        if edge == (Qt.Edge.TopEdge | Qt.Edge.LeftEdge) or edge == (Qt.Edge.BottomEdge | Qt.Edge.RightEdge):
            return Qt.CursorShape.SizeFDiagCursor
        return Qt.CursorShape.SizeBDiagCursor

    # ---- override cursor ----

    def _set_override_cursor(self, shape):
        if not self._override_cursor_active:
            QApplication.setOverrideCursor(shape)
            self._override_cursor_active = True

    def _restore_override_cursor(self):
        if self._override_cursor_active:
            QApplication.restoreOverrideCursor()
            self._override_cursor_active = False

    # ---- event filter ----

    def eventFilter(self, obj, event):
        if not self.store.frameless_mode or self.isMaximized():
            return super().eventFilter(obj, event)

        if isinstance(obj, QWidget) and obj.window() is not self:
            return super().eventFilter(obj, event)
        if QApplication.activeModalWidget() is not None:
            return super().eventFilter(obj, event)

        t = event.type()

        if t == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                pos = self.mapFromGlobal(event.globalPosition().toPoint())
                edge = self._hit_edge(pos)
                if edge is not None:
                    self._resize_edge = edge
                    self._resize_start_geo = self.geometry()
                    self._resize_start_pos = event.globalPosition().toPoint()
                    return True

        elif t == QEvent.Type.MouseMove:
            if self._resize_edge is not None:
                self._do_resize(event.globalPosition().toPoint())
                return True
            pos = self.mapFromGlobal(event.globalPosition().toPoint())
            edge = self._hit_edge(pos)
            if edge is not None:
                self._set_override_cursor(self._edge_cursor(edge))
            else:
                self._restore_override_cursor()

        elif t == QEvent.Type.MouseButtonRelease:
            if self._resize_edge is not None:
                self._resize_edge = None
                self._resize_start_geo = None
                self._resize_start_pos = None
                self._restore_override_cursor()
                return True

        elif t == QEvent.Type.Leave:
            if obj is self.centralWidget() and self._resize_edge is None:
                self._restore_override_cursor()

        return super().eventFilter(obj, event)

    # ---- resize ----

    def _do_resize(self, global_pos):
        delta = global_pos - self._resize_start_pos
        geo = self._resize_start_geo
        edge = self._resize_edge
        min_w, min_h = self.minimumWidth(), self.minimumHeight()

        top, left, right, bottom = geo.top(), geo.left(), geo.right(), geo.bottom()

        if edge & Qt.Edge.TopEdge:
            new_top = top + delta.y()
            if bottom - new_top >= min_h:
                top = new_top
        if edge & Qt.Edge.BottomEdge:
            new_bottom = bottom + delta.y()
            if new_bottom - top >= min_h:
                bottom = new_bottom
        if edge & Qt.Edge.LeftEdge:
            new_left = left + delta.x()
            if right - new_left >= min_w:
                left = new_left
        if edge & Qt.Edge.RightEdge:
            new_right = right + delta.x()
            if new_right - left >= min_w:
                right = new_right

        self.setGeometry(left, top, right - left, bottom - top)
