"""GameHub - 本地游戏管理系统兼启动器"""
import sys
from core.bootstrap import create_app

app, window = create_app()
window.show()
sys.exit(app.exec())
