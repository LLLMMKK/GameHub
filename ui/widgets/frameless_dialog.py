"""Shared frameless title bar helpers for dialogs."""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt

from ui.widgets.win_control_button import WinControlButton


class FramelessDialogTitleBar(QWidget):
    """Compact draggable title bar for modal dialogs."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("dialog-titlebar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 6, 8)
        layout.setSpacing(8)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("dialog-titlebar-title")
        layout.addWidget(self.title_label, 1)

        self.close_btn = WinControlButton("close")
        self.close_btn.setObjectName("dialog-close-btn")
        self.close_btn.clicked.connect(self.window().reject)
        layout.addWidget(self.close_btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.window().windowHandle():
            self.window().windowHandle().startSystemMove()
        super().mousePressEvent(event)


def apply_dialog_frameless(dialog):
    dialog.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
    dialog.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    dialog.setProperty("frameless", "true")
