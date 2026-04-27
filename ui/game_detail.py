"""游戏详情页面 - 封面与介绍并排，支持长文本滚动"""
import os
import webbrowser
from datetime import datetime
from urllib.parse import quote
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QTextEdit, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QColor, QFont

from core.game_model import Game
from ui.game_card import generate_default_cover, apply_mosaic, mask_name, _load_cover_pixmap, fit_cover_pixmap


_SEARCH_ENGINES = {
    "baidu": {
        "image": "https://image.baidu.com/search/index?tn=baiduimage&word={query}",
        "info": "https://www.baidu.com/s?wd={query}",
    },
    "bing": {
        "image": "https://www.bing.com/images/search?q={query}",
        "info": "https://www.bing.com/search?q={query}",
    },
    "google": {
        "image": "https://www.google.com/search?tbm=isch&q={query}",
        "info": "https://www.google.com/search?q={query}",
    },
}


class GameDetailPage(QWidget):
    """游戏详情页 - 替换卡片网格显示在主内容区"""

    play_clicked = pyqtSignal(str)
    edit_clicked = pyqtSignal(str)
    delete_clicked = pyqtSignal(str)
    back_clicked = pyqtSignal()
    cover_changed = pyqtSignal(str)
    desc_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.game: Game = None
        self._running = False
        self._info_values = {}  # key -> QLabel
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("detail-root")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── 顶部返回栏 ──
        top_bar = QWidget()
        top_bar.setFixedHeight(48)
        top_bar.setStyleSheet("background: transparent;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(24, 8, 24, 8)

        back_btn = QPushButton("←  返回游戏列表")
        back_btn.setObjectName("back-btn")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_clicked.emit)
        top_layout.addWidget(back_btn)
        top_layout.addStretch()
        outer.addWidget(top_bar)

        div = QFrame()
        div.setObjectName("divider")
        div.setFixedHeight(1)
        outer.addWidget(div)

        # ── 可滚动内容 ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(40, 32, 40, 40)
        content_layout.setSpacing(48)

        # === 左侧：封面 ===
        self.cover_label = QLabel()
        self.cover_label.setObjectName("detail-cover")
        self.cover_label.setFixedSize(315, 420)
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.cover_label)

        # === 右侧面板 ===
        right = QVBoxLayout()
        right.setSpacing(0)

        # 游戏名称
        self.title_label = QLabel()
        self.title_label.setObjectName("detail-title")
        self.title_label.setWordWrap(True)
        right.addWidget(self.title_label)

        right.addSpacing(6)

        # 分类 + R18 标签
        badges = QHBoxLayout()
        badges.setSpacing(8)

        self.category_label = QLabel()
        self.category_label.setObjectName("detail-category-tag")
        badges.addWidget(self.category_label)

        self.r18_label = QLabel("R18")
        self.r18_label.setObjectName("detail-r18-tag")
        self.r18_label.hide()
        badges.addWidget(self.r18_label)

        badges.addStretch()
        right.addLayout(badges)

        right.addSpacing(20)

        # 启动按钮
        self.play_btn = QPushButton("▶  启动游戏")
        self.play_btn.setObjectName("play-btn")
        self.play_btn.setProperty("running", "false")
        self.play_btn.setFixedHeight(56)
        self.play_btn.setMinimumWidth(240)
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.clicked.connect(self._on_play)
        f = self.play_btn.font()
        f.setBold(True)
        self.play_btn.setFont(f)
        right.addWidget(self.play_btn)

        right.addSpacing(28)

        # ── 游戏介绍卡片 ──
        desc_card = QWidget()
        desc_card.setObjectName("desc-card")
        desc_layout = QVBoxLayout(desc_card)

        desc_title = QLabel("游戏介绍")
        desc_title.setObjectName("desc-title")
        desc_layout.addWidget(desc_title)

        self.desc_content = QTextEdit()
        self.desc_content.setObjectName("desc-content")
        self.desc_content.setReadOnly(True)
        self.desc_content.setFrameShape(QFrame.Shape.NoFrame)
        self.desc_content.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.desc_content.setMaximumHeight(280)
        self.desc_content.setMinimumHeight(60)
        self.desc_content.setPlaceholderText("暂无介绍，点击下方「搜索信息」从网络获取")
        desc_layout.addWidget(self.desc_content)

        right.addWidget(desc_card)

        right.addSpacing(24)

        # ── 详细信息（2 列网格）─
        info_header = QLabel("详细信息")
        info_header.setObjectName("section-header")
        right.addWidget(info_header)

        right.addSpacing(10)

        info_grid = QGridLayout()
        info_grid.setSpacing(4)

        fields = [
            ("游玩时长", "time"),
            ("最近游玩", "last"),
            ("添加时间", "added"),
            ("游戏路径", "path"),
            ("启动参数", "args"),
        ]
        positions = [(0, 0), (0, 2), (1, 0), (1, 2), (2, 0)]

        for (label_text, key), (row, col) in zip(fields, positions):
            key_lbl = QLabel(label_text)
            key_lbl.setObjectName("info-key")
            info_grid.addWidget(key_lbl, row, col)

            val_lbl = QLabel("—")
            val_lbl.setObjectName("info-value")
            val_lbl.setWordWrap(True)
            val_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            info_grid.addWidget(val_lbl, row, col + 1)
            self._info_values[key] = val_lbl

        right.addLayout(info_grid)

        right.addSpacing(24)

        # ── 操作按钮 ──
        action_header = QLabel("操作")
        action_header.setObjectName("section-header")
        right.addWidget(action_header)

        right.addSpacing(10)

        action_row = QHBoxLayout()
        action_row.setSpacing(10)

        self.edit_btn = QPushButton("编辑信息")
        self.edit_btn.setObjectName("secondary-btn")
        self.edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.game.id if self.game else ""))
        action_row.addWidget(self.edit_btn)

        self.open_dir_btn = QPushButton("文件位置")
        self.open_dir_btn.setObjectName("secondary-btn")
        self.open_dir_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_dir_btn.clicked.connect(self._open_file_location)
        action_row.addWidget(self.open_dir_btn)

        self.delete_btn = QPushButton("删除游戏")
        self.delete_btn.setObjectName("secondary-btn")
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.clicked.connect(self._on_delete)
        f = self.delete_btn.font()
        f.setBold(True)
        self.delete_btn.setFont(f)
        action_row.addWidget(self.delete_btn)

        action_row.addStretch()
        right.addLayout(action_row)

        right.addSpacing(20)

        # ── 搜索区域 ──
        search_header = QLabel("搜索网络资源")
        search_header.setObjectName("section-header")
        right.addWidget(search_header)

        right.addSpacing(10)

        search_row = QHBoxLayout()
        search_row.setSpacing(10)

        self.search_cover_btn = QPushButton("搜索封面")
        self.search_cover_btn.setObjectName("secondary-btn")
        self.search_cover_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_cover_btn.clicked.connect(self._search_cover)
        search_row.addWidget(self.search_cover_btn)

        self.search_info_btn = QPushButton("搜索信息")
        self.search_info_btn.setObjectName("secondary-btn")
        self.search_info_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_info_btn.clicked.connect(self._search_info)
        search_row.addWidget(self.search_info_btn)

        self.search_steam_btn = QPushButton("Steam")
        self.search_steam_btn.setObjectName("secondary-btn")
        self.search_steam_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_steam_btn.clicked.connect(self._search_steam)
        search_row.addWidget(self.search_steam_btn)

        search_row.addStretch()
        right.addLayout(search_row)

        right.addStretch()

        content_layout.addLayout(right, 1)
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

    # ── 公共接口 ──

    def set_game(self, game: Game, running: bool = False):
        self.game = game
        self._running = running
        self._update_ui()

    def set_running(self, running: bool):
        self._running = running
        self._update_play_button()

    # ── 内部更新 ──

    def _update_ui(self):
        if not self.game:
            return

        game = self.game
        privacy = False
        parent = self.window()
        if hasattr(parent, 'store'):
            privacy = parent.store.privacy_mode

        # 封面
        if game.cover_path and os.path.exists(game.cover_path):
            pixmap = _load_cover_pixmap(game.cover_path)
            if not pixmap.isNull():
                scaled = fit_cover_pixmap(pixmap, 315, 420)
                if game.is_r18 and privacy:
                    scaled = apply_mosaic(scaled, block_size=13)
                self.cover_label.setPixmap(scaled)
            else:
                self._set_default_cover(privacy)
        else:
            self._set_default_cover(privacy)

        # 标题
        if game.is_r18 and privacy:
            self.title_label.setText(mask_name(game.name))
        else:
            self.title_label.setText(game.name)

        # 分类
        self.category_label.setText(game.category)

        # R18 标签
        self.r18_label.setVisible(game.is_r18)

        # 介绍
        self.desc_content.setPlainText(game.description or "")

        # 信息行
        self._info_values["time"].setText(game.format_play_time())
        self._info_values["last"].setText(game.format_last_played())
        self._info_values["added"].setText(
            datetime.fromisoformat(game.added_time).strftime("%Y-%m-%d %H:%M") if game.added_time else "—"
        )
        self._info_values["path"].setText(game.exe_path or "—")
        self._info_values["args"].setText(game.launch_args or "无")

        self._update_play_button()

    def _set_default_cover(self, privacy: bool):
        cover = generate_default_cover(self.game.name, 315, 420)
        if self.game.is_r18 and privacy:
            cover = apply_mosaic(cover, block_size=13)
        self.cover_label.setPixmap(cover)

    def _update_play_button(self):
        if self._running:
            self.play_btn.setText("■  关闭游戏")
        else:
            self.play_btn.setText("▶  启动游戏")
        self.play_btn.setProperty("running", str(self._running).lower())
        self.play_btn.style().unpolish(self.play_btn)
        self.play_btn.style().polish(self.play_btn)

    # ── 操作 ──

    def _on_play(self):
        if self.game:
            self.play_clicked.emit(self.game.id)

    def _on_delete(self):
        if self.game:
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self, "确认删除",
                f"确定要删除游戏 \"{self.game.name}\" 吗？\n（仅从列表移除，不会删除游戏文件）",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.delete_clicked.emit(self.game.id)

    def _open_file_location(self):
        if self.game and self.game.exe_path and os.path.exists(self.game.exe_path):
            import subprocess
            path = os.path.normpath(self.game.exe_path)
            subprocess.Popen(f'explorer /select,"{path}"')
        elif self.game and self.game.exe_path:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "提示", "游戏文件不存在，可能已被移动或删除")

    # ── 搜索 ──

    def _search_cover(self):
        if self.game:
            self._open_search("image")

    def _search_info(self):
        if self.game:
            self._open_search("info")

    def _search_steam(self):
        if self.game:
            self._open_search("steam")

    def _open_search(self, tab: str = "image"):
        if not self.game:
            return

        parent = self.window()
        data_dir = getattr(parent, 'store', None)
        if not data_dir:
            return
        data_dir = data_dir.data_dir
        game_id = self.game.id
        engine = parent.store.default_search_engine
        name = self.game.name

        engine_urls = _SEARCH_ENGINES.get(engine, _SEARCH_ENGINES["baidu"])

        if tab == "image":
            webbrowser.open(engine_urls["image"].format(query=quote(name + ' 游戏封面')))
        elif tab == "info":
            webbrowser.open(engine_urls["info"].format(query=quote(name + ' 游戏 介绍')))
        elif tab == "steam":
            webbrowser.open(f"https://store.steampowered.com/search/?term={quote(name)}")

        from ui.web_search_dialog import WebSearchDialog
        dlg = WebSearchDialog(name, data_dir, game_id, self)
        dlg.cover_selected.connect(self._on_cover_selected)
        dlg.desc_selected.connect(self._on_desc_selected)
        dlg.exec()

    def _on_cover_selected(self, path: str):
        if self.game:
            self.game.cover_path = path
            self.cover_changed.emit(path)
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                scaled = fit_cover_pixmap(pixmap, 315, 420)
                self.cover_label.setPixmap(scaled)

    def _on_desc_selected(self, text: str):
        if self.game:
            self.game.description = text
            self.desc_changed.emit(text)
            self.desc_content.setPlainText(text)
