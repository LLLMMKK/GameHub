"""GameHub - 无终端窗口启动器"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow
from ui.styles import DARK_STYLE


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE)
    app.setApplicationName("GameHub")
    app.setApplicationDisplayName("GameHub - 游戏管理器")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
