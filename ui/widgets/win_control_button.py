"""手绘窗口控制按钮（最小化/最大化/关闭）"""
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QPen


class WinControlButton(QPushButton):
    """手绘窗口控制按钮，避免 Unicode 字符在不同字体下对齐不一致"""

    def __init__(self, icon_type: str, parent=None):
        super().__init__(parent)
        self._icon_type = icon_type  # 'min', 'max', 'close'
        self._is_maximized = False
        self.setFixedSize(40, 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_maximized_state(self, state: bool):
        self._is_maximized = state
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        icon_color = self.palette().color(self.foregroundRole())
        pen = QPen(icon_color, 1.2)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2

        if self._icon_type == 'min':
            y = int(cy)
            x0, x1 = int(cx - 5), int(cx + 5)
            p.drawLine(x0, y, x1, y)
            p.drawLine(x0, y + 1, x1, y + 1)

        elif self._icon_type == 'max':
            if self._is_maximized:
                # 还原图标：前后两个错位方框
                s, ox, oy = 7, 2, -2
                back = QRectF(cx - s - ox, cy - s - oy, s * 2, s * 2)
                front = QRectF(cx - s + ox, cy - s + oy, s * 2, s * 2)
                parent_bg = self.window().palette().color(
                    self.window().backgroundRole())
                p.setBrush(parent_bg)
                p.drawRect(front)
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawRect(front)
                p.drawRect(back)
            else:
                s = 7
                p.drawRect(QRectF(cx - s, cy - s, s * 2, s * 2))

        elif self._icon_type == 'close':
            d = 5
            p.drawLine(int(cx - d), int(cy - d), int(cx + d), int(cy + d))
            p.drawLine(int(cx - d), int(cy + d), int(cx + d), int(cy - d))
            p.drawLine(int(cx - d), int(cy - d + 1), int(cx + d - 1), int(cy + d))
            p.drawLine(int(cx - d + 1), int(cy + d), int(cx + d), int(cy - d + 1))

        p.end()
