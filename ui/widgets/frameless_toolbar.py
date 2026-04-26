"""支持 frameless 模式拖拽的工具栏"""
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt


class FramelessToolbar(QWidget):
    """支持 frameless 模式拖拽的工具栏"""

    def __init__(self, is_frameless, parent=None):
        super().__init__(parent)
        self._is_frameless = is_frameless  # callable: () -> bool

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._is_frameless():
            self.window().windowHandle().startSystemMove()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self._is_frameless():
            win = self.window()
            if win.isMaximized():
                win.showNormal()
            else:
                win.showMaximized()
        super().mouseDoubleClickEvent(event)
