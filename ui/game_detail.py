"""游戏详情页面 - 全屏展示，封面与信息并排"""
import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGraphicsDropShadowEffect, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QColor, QFont

from core.game_model import Game
from ui.game_card import generate_default_cover, apply_mosaic, mask_name, _load_cover_pixmap


class GameDetailPage(QWidget):
    """游戏详情页 - 替换卡片网格显示在主内容区

    布局: [返回按钮]
          [大封面(左)] [信息面板(右): 游戏名 / 分类标签 / 启动按钮 / 详细信息 / 编辑删除]
    """
    play_clicked = pyqtSignal(str)
    edit_clicked = pyqtSignal(str)
    delete_clicked = pyqtSignal(str)
    back_clicked = pyqtSignal()
    cover_changed = pyqtSignal(str)   # 封面路径
    desc_changed = pyqtSignal(str)    # 介绍文本

    def __init__(self, parent=None):
        super().__init__(parent)
        self.game: Game = None
        self._running = False
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("background-color: #0e1621;")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # 顶部返回栏
        top_bar = QWidget()
        top_bar.setStyleSheet("background: transparent;")
        top_bar.setFixedHeight(48)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(24, 8, 24, 8)

        back_btn = QPushButton("←  返回游戏列表")
        back_btn.setObjectName("back-btn")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setToolTip("返回游戏列表")
        back_btn.clicked.connect(self.back_clicked.emit)
        top_layout.addWidget(back_btn)
        top_layout.addStretch()
        outer.addWidget(top_bar)

        # 分隔线
        div = QFrame()
        div.setObjectName("divider")
        div.setFixedHeight(1)
        outer.addWidget(div)

        # 滚动内容
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(40, 32, 40, 40)
        content_layout.setSpacing(40)

        # === 左侧：封面 + 简介 ===
        left = QVBoxLayout()
        left.setSpacing(12)
        left.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.cover_label = QLabel()
        self.cover_label.setFixedSize(315, 420)
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setStyleSheet("background-color: #141c28; border-radius: 12px;")

        # 封面阴影
        cover_shadow = QGraphicsDropShadowEffect(self)
        cover_shadow.setBlurRadius(30)
        cover_shadow.setColor(QColor(0, 0, 0, 100))
        cover_shadow.setOffset(0, 8)
        self.cover_label.setGraphicsEffect(cover_shadow)
        left.addWidget(self.cover_label)

        # 简介（紧跟封面下方）
        self.desc_label = QLabel()
        self.desc_label.setStyleSheet("color: #8fa3b8; font-size: 13px; background: transparent; line-height: 1.6;")
        self.desc_label.setWordWrap(True)
        self.desc_label.setMaximumWidth(315)
        self.desc_label.hide()
        left.addWidget(self.desc_label)

        left.addStretch()

        content_layout.addLayout(left)

        # === 右侧：信息 + 操作 ===
        right = QVBoxLayout()
        right.setSpacing(0)
        right.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 游戏名称
        self.title_label = QLabel()
        self.title_label.setStyleSheet(
            "color: #e8edf3; font-size: 32px; font-weight: bold; background: transparent;"
        )
        self.title_label.setWordWrap(True)
        right.addWidget(self.title_label)

        right.addSpacing(6)

        # 分类标签
        self.category_label = QLabel()
        self.category_label.setStyleSheet("""
            color: #3a7bd5;
            background-color: #141c28;
            border: 1px solid #1e2d3d;
            border-radius: 4px;
            padding: 3px 12px;
            font-size: 12px;
        """)
        right.addWidget(self.category_label)

        right.addSpacing(24)

        # === 启动按钮行（核心操作，突出显示）===
        self.play_btn = QPushButton("▶  启动游戏")
        self.play_btn.setObjectName("play-btn")
        self.play_btn.setFixedHeight(56)
        self.play_btn.setMinimumWidth(240)
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.setToolTip("启动或关闭游戏")

        play_shadow = QGraphicsDropShadowEffect(self)
        play_shadow.setBlurRadius(16)
        play_shadow.setColor(QColor(58, 138, 40, 80))
        play_shadow.setOffset(0, 4)
        self.play_btn.setGraphicsEffect(play_shadow)
        self.play_btn.clicked.connect(self._on_play)
        right.addWidget(self.play_btn)

        right.addSpacing(28)

        # --- 编辑/删除操作区 ---
        action_box = QWidget()
        action_box.setStyleSheet("background: #111820; border-radius: 10px;")
        action_layout = QHBoxLayout(action_box)
        action_layout.setContentsMargins(16, 12, 16, 12)
        action_layout.setSpacing(12)

        action_label = QLabel("游戏操作")
        action_label.setStyleSheet("color: #8fa3b8; font-size: 13px; font-weight: bold; background: transparent;")
        action_layout.addWidget(action_label)

        action_layout.addStretch()

        self.edit_btn = QPushButton("编辑信息")
        self.edit_btn.setObjectName("secondary-btn")
        self.edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_btn.setToolTip("编辑游戏信息")
        self.edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.game.id if self.game else ""))
        action_layout.addWidget(self.edit_btn)

        self.open_dir_btn = QPushButton("文件位置")
        self.open_dir_btn.setObjectName("secondary-btn")
        self.open_dir_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_dir_btn.setToolTip("在资源管理器中打开游戏所在目录")
        self.open_dir_btn.clicked.connect(self._open_file_location)
        action_layout.addWidget(self.open_dir_btn)

        self.delete_btn = QPushButton("删除游戏")
        self.delete_btn.setObjectName("danger-btn")
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.setToolTip("从列表中移除游戏")
        self.delete_btn.clicked.connect(self._on_delete)
        action_layout.addWidget(self.delete_btn)

        right.addWidget(action_box)

        right.addSpacing(20)

        # 详细信息区域
        info_header = QLabel("详细信息")
        info_header.setStyleSheet("color: #8fa3b8; font-size: 14px; font-weight: bold; background: transparent; letter-spacing: 1px;")
        right.addWidget(info_header)

        right.addSpacing(12)

        # 信息行
        self._info_rows = {}
        for key, label in [
            ("time", "🎮  游玩时长"),
            ("last", "🕐  最近游玩"),
            ("added", "📅  添加时间"),
            ("path", "📁  游戏路径"),
            ("args", "⚙  启动参数"),
        ]:
            row = self._make_info_row(label)
            self._info_rows[key] = row
            right.addWidget(row)

        right.addSpacing(20)

        # --- 搜索网络资源区 ---
        search_box = QWidget()
        search_box.setStyleSheet("background: #111820; border-radius: 10px;")
        search_layout = QVBoxLayout(search_box)
        search_layout.setContentsMargins(16, 12, 16, 12)
        search_layout.setSpacing(10)

        search_header = QLabel("搜索网络资源")
        search_header.setStyleSheet("color: #8fa3b8; font-size: 13px; font-weight: bold; background: transparent;")
        search_layout.addWidget(search_header)

        search_row = QHBoxLayout()
        search_row.setSpacing(10)

        self.search_cover_btn = QPushButton("🔍 搜索封面")
        self.search_cover_btn.setObjectName("secondary-btn")
        self.search_cover_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_cover_btn.setToolTip("搜索游戏封面图片")
        self.search_cover_btn.clicked.connect(self._search_cover)
        search_row.addWidget(self.search_cover_btn)

        self.search_info_btn = QPushButton("🌐 搜索信息")
        self.search_info_btn.setObjectName("secondary-btn")
        self.search_info_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_info_btn.setToolTip("搜索游戏相关信息")
        self.search_info_btn.clicked.connect(self._search_info)
        search_row.addWidget(self.search_info_btn)

        self.search_steam_btn = QPushButton("🎮 Steam")
        self.search_steam_btn.setObjectName("secondary-btn")
        self.search_steam_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_steam_btn.setToolTip("在 Steam 商店中搜索")
        self.search_steam_btn.clicked.connect(self._search_steam)
        search_row.addWidget(self.search_steam_btn)

        search_row.addStretch()
        search_layout.addLayout(search_row)

        right.addWidget(search_box)

        right.addStretch()

        content_layout.addLayout(right, 1)

        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

    def _make_info_row(self, label: str) -> QWidget:
        """创建信息行"""
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        lbl = QLabel(label)
        lbl.setStyleSheet("color: #4a6080; font-size: 12px; background: transparent;")
        layout.addWidget(lbl)

        value = QLabel("—")
        value.setObjectName("detail-info-value")
        value.setWordWrap(True)
        value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(value)

        # 底部间距
        spacer = QWidget()
        spacer.setFixedHeight(12)
        spacer.setStyleSheet("background: transparent;")
        layout.addWidget(spacer)

        row._value_label = value
        return row

    def set_game(self, game: Game, running: bool = False):
        self.game = game
        self._running = running
        self._update_ui()

    def _update_ui(self):
        if not self.game:
            return

        game = self.game

        # 检查隐私模式
        privacy = False
        parent = self.window()
        if hasattr(parent, 'store'):
            privacy = parent.store.privacy_mode

        # 封面
        if game.cover_path and os.path.exists(game.cover_path):
            pixmap = _load_cover_pixmap(game.cover_path)
            if not pixmap.isNull():
                # 先 scale 到目标尺寸再 mosaic，效果清晰锐利
                scaled = pixmap.scaled(315, 420, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                       Qt.TransformationMode.SmoothTransformation)
                if game.is_r18 and privacy:
                    scaled = apply_mosaic(scaled, block_size=13)
                self.cover_label.setPixmap(scaled)
            else:
                cover = generate_default_cover(game.name, 320, 420)
                if game.is_r18 and privacy:
                    cover = apply_mosaic(cover, block_size=13)
                self.cover_label.setPixmap(cover)
        else:
            cover = generate_default_cover(game.name, 320, 420)
            if game.is_r18 and privacy:
                cover = apply_mosaic(cover, block_size=13)
            self.cover_label.setPixmap(cover)

        # 标题
        if game.is_r18 and privacy:
            self.title_label.setText(mask_name(game.name))
        else:
            self.title_label.setText(game.name)

        # 分类
        self.category_label.setText(game.category)

        # 介绍
        if game.description:
            self.desc_label.setText(game.description)
            self.desc_label.show()
        else:
            self.desc_label.hide()

        # 信息行
        self._info_rows["time"]._value_label.setText(game.format_play_time())
        self._info_rows["last"]._value_label.setText(game.format_last_played())
        self._info_rows["added"]._value_label.setText(
            datetime.fromisoformat(game.added_time).strftime("%Y-%m-%d %H:%M") if game.added_time else "—"
        )
        self._info_rows["path"]._value_label.setText(game.exe_path or "—")
        self._info_rows["args"]._value_label.setText(game.launch_args or "无")

        # 启动按钮
        self._update_play_button()

    def _update_play_button(self):
        if self._running:
            self.play_btn.setText("■  关闭游戏")
            self.play_btn.setProperty("running", "true")
            shadow = self.play_btn.graphicsEffect()
            if shadow:
                shadow.setColor(QColor(192, 57, 43, 80))
        else:
            self.play_btn.setText("▶  启动游戏")
            self.play_btn.setProperty("running", "false")
            shadow = self.play_btn.graphicsEffect()
            if shadow:
                shadow.setColor(QColor(58, 138, 40, 80))

        self.play_btn.style().unpolish(self.play_btn)
        self.play_btn.style().polish(self.play_btn)

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

    def set_running(self, running: bool):
        self._running = running
        self._update_play_button()

    def _open_file_location(self):
        if self.game and self.game.exe_path and os.path.exists(self.game.exe_path):
            import subprocess
            path = os.path.normpath(self.game.exe_path)
            subprocess.Popen(f'explorer /select,"{path}"')
        elif self.game and self.game.exe_path:
            QMessageBox.information(self, "提示", "游戏文件不存在，可能已被移动或删除")

    def _search_cover(self):
        if self.game:
            self._open_search("image")

    def _search_info(self):
        if self.game:
            self._open_search("info")

    def _search_steam(self):
        if self.game:
            self._open_search("steam")

    # 搜索引擎 URL 映射
    SEARCH_ENGINES = {
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

    def _open_search(self, tab: str = "image"):
        if not self.game:
            return
        import webbrowser
        from urllib.parse import quote
        from ui.web_search_dialog import WebSearchDialog
        # 找到主窗口获取 data_dir
        parent = self.window()
        data_dir = ""
        game_id = self.game.id
        engine = "baidu"
        if hasattr(parent, 'store'):
            data_dir = parent.store.data_dir
            engine = parent.store.default_search_engine
        if not data_dir:
            return

        name = self.game.name
        engine_urls = self.SEARCH_ENGINES.get(engine, self.SEARCH_ENGINES["baidu"])

        # 先在浏览器中打开对应搜索
        if tab == "image":
            url = engine_urls["image"].format(query=quote(name + ' 游戏封面'))
            webbrowser.open(url)
        elif tab == "info":
            url = engine_urls["info"].format(query=quote(name + ' 游戏 介绍'))
            webbrowser.open(url)
        elif tab == "steam":
            webbrowser.open(f"https://store.steampowered.com/search/?term={quote(name)}")

        dlg = WebSearchDialog(name, data_dir, game_id, self)
        dlg.cover_selected.connect(self._on_cover_selected)
        dlg.desc_selected.connect(self._on_desc_selected)
        dlg.exec()

    def _on_cover_selected(self, path: str):
        if self.game:
            self.game.cover_path = path
            self.cover_changed.emit(path)
            # 刷新封面显示
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(315, 420, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                       Qt.TransformationMode.SmoothTransformation)
                self.cover_label.setPixmap(scaled)

    def _on_desc_selected(self, text: str):
        if self.game:
            self.game.description = text
            self.desc_changed.emit(text)
            self.desc_label.setText(text)
            self.desc_label.show()
