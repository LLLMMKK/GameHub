"""GameHub - 本地游戏管理系统兼启动器"""
import sys
import os

# 将项目根目录加入 sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow
from ui.styles import THEMES, DARK_STYLE


def _load_theme():
    """从 config.json 读取主题设置"""
    import json
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config.get("theme", "暗夜")
    except (FileNotFoundError, json.JSONDecodeError):
        return "暗夜"


def main():
    app = QApplication(sys.argv)
    theme = _load_theme()
    app.setStyleSheet(THEMES.get(theme, DARK_STYLE))
    app.setApplicationName("GameHub")
    app.setApplicationDisplayName("GameHub - 游戏管理器")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
