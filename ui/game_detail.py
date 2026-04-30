"""游戏详情页面 - 封面与介绍并排，支持长文本滚动"""
import os
from datetime import datetime
from urllib.parse import quote
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QTextEdit, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF
from PyQt6.QtGui import QPixmap, QColor, QFont, QPainter, QPainterPath

from core.game_model import Game
from ui.game_card import generate_default_cover, apply_mosaic, mask_name, _load_cover_pixmap, fit_cover_pixmap


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
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(34, 28, 34, 40)
        content_layout.setSpacing(18)

        self.hero_panel = QWidget()
        self.hero_panel.setObjectName("detail-hero")
        self.hero_panel.setFixedHeight(436)
        hero_layout = QHBoxLayout(self.hero_panel)
        hero_layout.setContentsMargins(28, 28, 28, 28)
        hero_layout.setSpacing(28)

        self.cover_label = QLabel()
        self.cover_label.setObjectName("detail-cover")
        self.cover_label.setFixedSize(285, 380)
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.addWidget(self.cover_label, 0, Qt.AlignmentFlag.AlignTop)

        hero_main = QVBoxLayout()
        hero_main.setSpacing(12)

        self.category_label = QLabel()
        self.category_label.setObjectName("detail-category-tag")
        hero_main.addWidget(self.category_label, 0, Qt.AlignmentFlag.AlignLeft)

        self.title_label = QLabel()
        self.title_label.setObjectName("detail-title")
        self.title_label.setWordWrap(True)
        hero_main.addWidget(self.title_label)

        badges = QHBoxLayout()
        badges.setSpacing(8)

        self.r18_label = QLabel("私密")
        self.r18_label.setObjectName("detail-r18-tag")
        self.r18_label.hide()
        badges.addWidget(self.r18_label)

        self.completed_label = QLabel("已通关")
        self.completed_label.setObjectName("detail-completed-tag")
        self.completed_label.hide()
        badges.addWidget(self.completed_label)

        badges.addStretch()
        hero_main.addLayout(badges)
        hero_main.addStretch()

        self.play_btn = QPushButton("▶  启动游戏")
        self.play_btn.setObjectName("play-btn")
        self.play_btn.setProperty("running", "false")
        self.play_btn.setFixedHeight(52)
        self.play_btn.setMinimumWidth(220)
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.clicked.connect(self._on_play)
        f = self.play_btn.font()
        f.setBold(True)
        self.play_btn.setFont(f)
        hero_main.addWidget(self.play_btn, 0, Qt.AlignmentFlag.AlignLeft)

        action_bar = QWidget()
        action_bar.setObjectName("detail-action-bar")
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(8)

        self.import_btn = QPushButton("素材导入")
        self.import_btn.setObjectName("secondary-btn")
        self.import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.import_btn.clicked.connect(self._open_resource_dialog)
        action_layout.addWidget(self.import_btn)

        self.search_steam_btn = QPushButton("Steam")
        self.search_steam_btn.setObjectName("secondary-btn")
        self.search_steam_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_steam_btn.clicked.connect(self._search_steam)
        action_layout.addWidget(self.search_steam_btn)

        self.more_btn = QPushButton("更多")
        self.more_btn.setObjectName("secondary-btn")
        self.more_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._action_menu = QMenu(self.more_btn)
        self._action_menu.setObjectName("detail-action-menu")
        edit_action = self._action_menu.addAction("编辑信息")
        edit_action.triggered.connect(lambda: self.edit_clicked.emit(self.game.id if self.game else ""))
        open_dir_action = self._action_menu.addAction("文件位置")
        open_dir_action.triggered.connect(self._open_file_location)
        self._action_menu.addSeparator()
        delete_action = self._action_menu.addAction("删除游戏")
        delete_action.triggered.connect(self._on_delete)
        self.more_btn.clicked.connect(lambda: self._action_menu.exec(self.more_btn.mapToGlobal(self.more_btn.rect().bottomLeft())))
        action_layout.addWidget(self.more_btn)
        action_layout.addStretch()
        hero_main.addWidget(action_bar)
        hero_layout.addLayout(hero_main, 1)

        meta_card = QWidget()
        meta_card.setObjectName("detail-meta-card")
        meta_layout = QVBoxLayout(meta_card)
        meta_layout.setContentsMargins(18, 18, 18, 18)
        meta_layout.setSpacing(12)

        meta_header = QLabel("运行档案")
        meta_header.setObjectName("section-header")
        meta_layout.addWidget(meta_header)

        fields = [
            ("游玩时长", "time"),
            ("最近游玩", "last"),
            ("添加时间", "added"),
            ("游戏路径", "path"),
            ("启动参数", "args"),
        ]

        for label_text, key in fields:
            key_lbl = QLabel(label_text)
            key_lbl.setObjectName("info-key")
            meta_layout.addWidget(key_lbl)

            val_lbl = QLabel("—")
            val_lbl.setObjectName("info-value")
            val_lbl.setWordWrap(True)
            val_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            meta_layout.addWidget(val_lbl)
            self._info_values[key] = val_lbl

        meta_layout.addStretch()
        hero_layout.addWidget(meta_card, 0, Qt.AlignmentFlag.AlignTop)
        content_layout.addWidget(self.hero_panel)

        desc_card = QWidget()
        desc_card.setObjectName("desc-card")
        desc_layout = QVBoxLayout(desc_card)
        desc_layout.setContentsMargins(22, 20, 22, 20)
        desc_layout.setSpacing(12)

        desc_title = QLabel("游戏介绍")
        desc_title.setObjectName("desc-title")
        desc_layout.addWidget(desc_title)

        self.desc_content = QTextEdit()
        self.desc_content.setObjectName("desc-content")
        self.desc_content.setReadOnly(True)
        self.desc_content.setFrameShape(QFrame.Shape.NoFrame)
        self.desc_content.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.desc_content.setMaximumHeight(320)
        self.desc_content.setMinimumHeight(120)
        self.desc_content.setPlaceholderText("暂无介绍，可通过「素材导入」从网络资料中粘贴保存")
        desc_layout.addWidget(self.desc_content)
        content_layout.addWidget(desc_card)

        content_layout.addStretch()
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
                self._set_cover_visual(pixmap, privacy)
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

        # 私密标签
        self.r18_label.setVisible(game.is_r18)
        self.completed_label.setVisible(game.is_completed)

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
        cover = generate_default_cover(self.game.name, 285, 380)
        if self.game.is_r18 and privacy:
            cover = apply_mosaic(cover, block_size=13)
        self.cover_label.setPixmap(self._round_pixmap(cover))
        self._set_hero_background(cover)

    def _set_cover_visual(self, pixmap: QPixmap, privacy: bool):
        cover = fit_cover_pixmap(pixmap, 285, 380)
        if self.game.is_r18 and privacy:
            cover = apply_mosaic(cover, block_size=13)
        self.cover_label.setPixmap(self._round_pixmap(cover))
        self._set_hero_background(cover)

    def _set_hero_background(self, pixmap: QPixmap):
        if pixmap.isNull():
            return
        color = self._average_color(pixmap).darker(145)
        r, g, b = color.red(), color.green(), color.blue()
        self.hero_panel.setStyleSheet(
            "#detail-hero {"
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
            f"stop:0 rgba({r},{g},{b},160), stop:1 rgba(10,14,20,210));"
            "border: 1px solid rgba(255,255,255,34);"
            "border-radius: 16px;"
            "}"
        )

    def _average_color(self, pixmap: QPixmap) -> QColor:
        image = pixmap.toImage().scaled(18, 18, Qt.AspectRatioMode.IgnoreAspectRatio,
                                        Qt.TransformationMode.SmoothTransformation)
        red = green = blue = count = 0
        for x in range(image.width()):
            for y in range(image.height()):
                color = QColor(image.pixel(x, y))
                if color.alpha() <= 0:
                    continue
                red += color.red()
                green += color.green()
                blue += color.blue()
                count += 1
        if not count:
            return QColor(35, 46, 58)
        return QColor(red // count, green // count, blue // count)

    def _round_pixmap(self, pixmap: QPixmap, radius: int = 12) -> QPixmap:
        if pixmap.isNull():
            return pixmap
        result = QPixmap(pixmap.size())
        result.fill(Qt.GlobalColor.transparent)
        path = QPainterPath()
        path.addRoundedRect(QRectF(result.rect()), radius, radius)
        painter = QPainter(result)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        return result

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
            self.delete_clicked.emit(self.game.id)

    def _open_file_location(self):
        if self.game and self.game.exe_path and os.path.exists(self.game.exe_path):
            import subprocess
            path = os.path.normpath(self.game.exe_path)
            subprocess.Popen(f'explorer /select,"{path}"')
        elif self.game and self.game.exe_path:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "提示", "游戏文件不存在，可能已被移动或删除")

    def _search_steam(self):
        if self.game:
            import webbrowser
            webbrowser.open(f"https://store.steampowered.com/search/?term={quote(self.game.name)}")

    def _open_resource_dialog(self):
        if not self.game:
            return

        parent = self.window()
        data_dir = getattr(parent, 'store', None)
        if not data_dir:
            return
        data_dir = data_dir.data_dir
        game_id = self.game.id
        name = self.game.name

        from ui.web_search_dialog import WebSearchDialog
        dlg = WebSearchDialog(name, data_dir, game_id, self)
        dlg.cover_selected.connect(self._on_cover_selected)
        dlg.desc_selected.connect(self._on_desc_selected)
        dlg.exec()

    def _on_cover_selected(self, path: str):
        if self.game:
            self.game.cover_path = path
            self.cover_changed.emit(path)
            self._update_ui()

    def _on_desc_selected(self, text: str):
        if self.game:
            self.game.description = text
            self.desc_changed.emit(text)
            self.desc_content.setPlainText(text)
