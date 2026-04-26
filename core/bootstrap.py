"""共享启动逻辑 — 被 main.py 和 GameHub.pyw 复用"""
import sys
import os
import ctypes
import json


def _get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_theme(base_dir: str) -> str:
    config_path = os.path.join(base_dir, "data", "config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config.get("theme", "暗夜")
    except (FileNotFoundError, json.JSONDecodeError):
        return "暗夜"


def create_app() -> tuple:
    """创建并返回 (QApplication, MainWindow)"""
    base_dir = _get_base_dir()
    sys.path.insert(0, base_dir)

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QIcon
    from ui.main_window import MainWindow
    from ui.styles import THEMES, DARK_STYLE

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("GameHub.GameManager")

    app = QApplication(sys.argv)
    theme = _load_theme(base_dir)
    app.setStyleSheet(THEMES.get(theme, DARK_STYLE))
    app.setApplicationName("GameHub")
    app.setApplicationDisplayName("GameHub - 游戏管理器")

    icon_path = os.path.join(base_dir, "ui", "icon.ico")
    app_icon = QIcon(icon_path)
    app.setWindowIcon(app_icon)

    window = MainWindow()
    window.setWindowIcon(app_icon)

    return app, window
