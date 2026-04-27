"""扫描结果对话框 - 展示扫描到的游戏列表，支持逐条移除后批量添加，标记已有游戏"""
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QWidget
)
from PyQt6.QtCore import Qt

from core.game_model import Game

class ScanResultDialog(QDialog):
    """扫描结果对话框"""

    # 自定义返回码：用户点了"继续添加"
    ADD_MORE_RESULT = 10

    def __init__(self, games: list[Game], parent=None, allow_add_more: bool = False,
                 existing_paths: set[str] = None, existing_names: set[str] = None):
        super().__init__(parent)
        self._games = list(games)
        self._allow_add_more = allow_add_more
        self._existing_paths = existing_paths or set()
        self._existing_names = existing_names or set()
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("扫描结果")
        self.setMinimumWidth(560)
        self.setMinimumHeight(400)
        self.resize(640, 500)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 标题
        title = QLabel(f"找到 {len(self._games)} 个游戏")
        title.setObjectName("dialog-title")
        layout.addWidget(title)

        hint = QLabel("确认要添加的游戏，可以移除不需要的条目")
        hint.setObjectName("dialog-hint")
        layout.addWidget(hint)

        # 滚动列表
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self._list_widget = QWidget()
        self._list_widget.setStyleSheet("background: transparent;")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(4)
        self._list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self._list_widget)
        layout.addWidget(scroll, 1)

        # 底部按钮
        btn_row = QHBoxLayout()

        self._count_label = QLabel(f"已选 {len(self._games)} 项")
        self._count_label.setObjectName("dialog-muted")
        btn_row.addWidget(self._count_label)

        btn_row.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("secondary-btn")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        if self._allow_add_more:
            more_btn = QPushButton("继续添加")
            more_btn.setObjectName("toolbar-btn")
            more_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            more_btn.setToolTip("从其他目录继续选择文件")
            more_btn.clicked.connect(self._on_add_more)
            btn_row.addWidget(more_btn)

        self._add_btn = QPushButton("全部添加")
        self._add_btn.setObjectName("primary-btn")
        self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_btn.clicked.connect(self._on_add)
        btn_row.addWidget(self._add_btn)

        layout.addLayout(btn_row)

        # 填充列表
        self._refresh_list()

    def _refresh_list(self):
        """刷新游戏列表"""
        # 清除旧项
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, game in enumerate(self._games):
            row = self._make_game_row(game, i)
            self._list_layout.addWidget(row)

        self._count_label.setText(f"已选 {len(self._games)} 项")
        self._add_btn.setEnabled(len(self._games) > 0)

    def _make_game_row(self, game: Game, index: int) -> QWidget:
        """创建单行游戏条目"""
        norm_path = os.path.normpath(game.exe_path).lower()
        path_exists = norm_path in self._existing_paths
        name_exists = not path_exists and game.name.lower() in self._existing_names
        duplicate_state = "path" if path_exists else ("name" if name_exists else "none")

        row = QWidget()
        row.setObjectName("scan-result-row")
        row.setProperty("duplicate", duplicate_state)

        layout = QHBoxLayout(row)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # 游戏名称
        name_label = QLabel(game.name)
        name_label.setObjectName("scan-game-name")
        name_label.setProperty("duplicate", duplicate_state)
        name_label.setMinimumWidth(120)
        layout.addWidget(name_label)

        # 重复标记
        if path_exists:
            dup_label = QLabel("已添加")
            dup_label.setObjectName("duplicate-path-tag")
            layout.addWidget(dup_label)
        elif name_exists:
            dup_label = QLabel("同名")
            dup_label.setObjectName("duplicate-name-tag")
            layout.addWidget(dup_label)

        # 目录路径
        dir_path = os.path.dirname(game.exe_path) or game.exe_path
        path_label = QLabel(dir_path)
        path_label.setObjectName("dialog-subtle")
        path_label.setWordWrap(True)
        path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(path_label, 1)

        # 移除按钮
        remove_btn = QPushButton("移除")
        remove_btn.setFixedSize(52, 26)
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_btn.setObjectName("small-delete-btn")
        remove_btn.clicked.connect(lambda checked, idx=index: self._remove_item(idx))
        layout.addWidget(remove_btn)

        return row

    def _remove_item(self, index: int):
        """移除指定条目"""
        if 0 <= index < len(self._games):
            self._games.pop(index)
            self._refresh_list()

    def _on_add(self):
        """确认添加"""
        self.accept()

    def _on_add_more(self):
        """继续添加更多文件"""
        self.done(self.ADD_MORE_RESULT)

    def get_selected_games(self) -> list[Game]:
        """获取用户保留的游戏列表（排除路径已存在的）"""
        return [g for g in self._games
                if os.path.normpath(g.exe_path).lower() not in self._existing_paths]
