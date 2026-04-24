"""游戏卡片组件 - 精美版"""
import os
from functools import lru_cache

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGraphicsDropShadowEffect, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QBrush, QLinearGradient

from core.game_model import Game


def apply_mosaic(pixmap: QPixmap, block_size=12) -> QPixmap:
    """对 QPixmap 做像素化马赛克处理

    原理：先放大获取充足色彩 → 缩小采样 → 最近邻放大回原尺寸。
    类似"截图后马赛克"效果：色块边界清晰，颜色准确。
    """
    if pixmap.isNull():
        return pixmap
    w, h = pixmap.width(), pixmap.height()
    # 1. 放大4x，让低分辨率封面也有充足色彩信息
    big = pixmap.scaled(w * 4, h * 4,
                        Qt.AspectRatioMode.IgnoreAspectRatio,
                        Qt.TransformationMode.SmoothTransformation)
    # 2. 缩小采样：每个马赛克块对应约1像素
    small_w = max(w // block_size, 1)
    small_h = max(h // block_size, 1)
    small = big.scaled(small_w, small_h,
                       Qt.AspectRatioMode.IgnoreAspectRatio,
                       Qt.TransformationMode.SmoothTransformation)
    # 3. FastTransformation放大 → 清晰的像素块边界
    result = small.scaled(w, h,
                          Qt.AspectRatioMode.IgnoreAspectRatio,
                          Qt.TransformationMode.FastTransformation)
    return result


def mask_name(name: str) -> str:
    """名称遮蔽：保留首尾各1字，中间用 *** 替代"""
    if len(name) <= 2:
        return name[0] + "***" if name else "***"
    return name[0] + "***" + name[-1]


@lru_cache(maxsize=128)
def generate_default_cover(name: str, width=260, height=340) -> QPixmap:
    """根据游戏名首字母生成默认封面 - 渐变色+首字母"""
    pixmap = QPixmap(width, height)

    # 根据名称生成稳定的颜色对
    color_index = sum(ord(c) for c in name) % 10
    palettes = [
        ((41, 128, 185), (22, 70, 110)),    # 蓝
        ((142, 68, 173), (80, 30, 110)),     # 紫
        ((39, 174, 96), (18, 90, 50)),       # 绿
        ((211, 84, 0), (130, 50, 0)),        # 橙
        ((192, 57, 43), (120, 30, 20)),      # 红
        ((22, 160, 133), (10, 90, 75)),      # 青
        ((52, 152, 219), (25, 85, 130)),     # 亮蓝
        ((155, 89, 182), (95, 45, 115)),     # 淡紫
        ((230, 126, 34), (150, 70, 10)),     # 亮橙
        ((46, 64, 83), (20, 35, 48)),        # 深蓝灰
    ]
    (r1, g1, b1), (r2, g2, b2) = palettes[color_index]

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 对角线渐变
    gradient = QLinearGradient(0, 0, width, height)
    gradient.setColorAt(0.0, QColor(r1, g1, b1))
    gradient.setColorAt(0.5, QColor((r1 + r2) // 2, (g1 + g2) // 2, (b1 + b2) // 2))
    gradient.setColorAt(1.0, QColor(r2, g2, b2))
    painter.fillRect(0, 0, width, height, QBrush(gradient))

    # 装饰性半透明圆
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(255, 255, 255, 15))
    painter.drawEllipse(-30, -30, width // 2, width // 2)
    painter.drawEllipse(width // 3, height // 2, width // 2, width // 2)

    # 首字母
    initial = name[0].upper() if name else "?"
    font = QFont("Microsoft YaHei", 90)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QColor(255, 255, 255, 160))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, initial)

    # 底部小字
    if len(name) > 1:
        small_font = QFont("Microsoft YaHei", 14)
        small_font.setBold(False)
        painter.setFont(small_font)
        painter.setPen(QColor(255, 255, 255, 80))
        rect = pixmap.rect()
        rect.setTop(rect.top() + rect.height() // 2 + 40)
        painter.drawText(rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, name[:12])

    painter.end()
    return pixmap


class GameCard(QWidget):
    """游戏卡片 - 封面、名称、时长、播放按钮"""
    play_clicked = pyqtSignal(str)    # game_id
    detail_clicked = pyqtSignal(str)  # game_id
    delete_clicked = pyqtSignal(str)  # game_id

    CARD_WIDTH = 210
    COVER_HEIGHT = 280

    def __init__(self, game: Game, parent=None):
        super().__init__(parent)
        self.game = game
        self._running = game.is_running
        self._privacy_mode = False
        self.setObjectName("game-card")
        self.setFixedSize(self.CARD_WIDTH, self.COVER_HEIGHT + 80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self._hover = False
        self._setup_ui()
        self._load_cover()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 封面区域（含悬浮播放按钮）
        self._cover_container = QWidget()
        self._cover_container.setObjectName("game-cover")
        cover_layout = QVBoxLayout(self._cover_container)
        cover_layout.setContentsMargins(0, 0, 0, 0)
        cover_layout.setSpacing(0)

        self.cover_label = QLabel()
        self.cover_label.setFixedSize(self.CARD_WIDTH, self.COVER_HEIGHT)
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setScaledContents(True)
        cover_layout.addWidget(self.cover_label)

        # 悬浮播放遮罩
        self._overlay = QWidget(self._cover_container)
        self._overlay.setFixedSize(self.CARD_WIDTH, self.COVER_HEIGHT)
        self._overlay.setStyleSheet("background-color: rgba(0,0,0,0.45); border-radius: 9px 9px 0 0;")
        self._overlay.hide()

        overlay_layout = QVBoxLayout(self._overlay)
        overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 大播放按钮
        self._big_play_btn = QPushButton("▶" if not self._running else "■")
        self._big_play_btn.setObjectName("card-play-btn")
        self._big_play_btn.setFixedSize(56, 56)
        self._big_play_btn.setProperty("running", str(self._running).lower())
        self._big_play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._big_play_btn.setToolTip("启动游戏" if not self._running else "关闭游戏")
        self._big_play_btn.setStyleSheet("""
            #card-play-btn {
                background-color: rgba(58, 138, 40, 200);
                border: 2px solid rgba(92, 176, 64, 150);
                border-radius: 28px;
                color: white;
                font-size: 22px;
                font-weight: bold;
            }
            #card-play-btn:hover {
                background-color: rgba(92, 176, 64, 220);
                border-color: rgba(92, 176, 64, 200);
            }
            #card-play-btn[running="true"] {
                background-color: rgba(192, 57, 43, 200);
                border-color: rgba(231, 76, 60, 150);
            }
            #card-play-btn[running="true"]:hover {
                background-color: rgba(231, 76, 60, 220);
            }
        """)
        self._big_play_btn.clicked.connect(self._on_play)
        overlay_layout.addWidget(self._big_play_btn)

        # 提示文字
        self._overlay_hint = QLabel("启动游戏" if not self._running else "关闭游戏")
        self._overlay_hint.setStyleSheet("color: rgba(255,255,255,180); font-size: 12px; background: transparent; border: none;")
        self._overlay_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay_layout.addWidget(self._overlay_hint)

        layout.addWidget(self._cover_container)

        # 信息区域
        info_widget = QWidget()
        info_widget.setStyleSheet("background-color: transparent;")
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(10, 8, 10, 8)
        info_layout.setSpacing(3)

        # 名称
        display_name = mask_name(self.game.name) if (self.game.is_r18 and self._privacy_mode) else self.game.name
        self.title_label = QLabel(display_name)
        self.title_label.setObjectName("game-title")
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(38)
        self.title_label.setToolTip(self.game.name)
        info_layout.addWidget(self.title_label)

        # 底部行：分类标签 + R18标签 + 时长 + 小播放按钮
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(6)

        # 分类小标签
        if self.game.category and self.game.category != "其他":
            cat_label = QLabel(self.game.category)
            cat_label.setStyleSheet("""
                color: #3a7bd5;
                background-color: #141c28;
                border: 1px solid #1e2d3d;
                border-radius: 3px;
                padding: 1px 6px;
                font-size: 10px;
            """)
            bottom_row.addWidget(cat_label)

        # R18 红色标签
        if self.game.is_r18:
            r18_label = QLabel("R18")
            r18_label.setStyleSheet("""
                color: #ff4444;
                background-color: #2a0a0a;
                border: 1px solid #ff4444;
                border-radius: 3px;
                padding: 1px 5px;
                font-size: 9px;
                font-weight: bold;
            """)
            bottom_row.addWidget(r18_label)

        self.time_label = QLabel(self.game.format_play_time())
        self.time_label.setObjectName("game-time")
        bottom_row.addWidget(self.time_label)

        bottom_row.addStretch()

        # 小播放按钮（始终可见）
        self.play_btn = QPushButton("▶")
        self.play_btn.setObjectName("card-play-btn")
        self.play_btn.setFixedSize(32, 24)
        self.play_btn.setProperty("running", str(self._running).lower())
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.setToolTip("启动游戏" if not self._running else "关闭游戏")
        self.play_btn.setStyleSheet("""
            #card-play-btn {
                background-color: #2d6b1e;
                border: none;
                border-radius: 12px;
                color: white;
                font-size: 11px;
                font-weight: bold;
            }
            #card-play-btn:hover {
                background-color: #3a8a28;
            }
            #card-play-btn[running="true"] {
                background-color: #96281b;
            }
            #card-play-btn[running="true"]:hover {
                background-color: #c0392b;
            }
        """)
        self.play_btn.clicked.connect(self._on_play)
        bottom_row.addWidget(self.play_btn)

        info_layout.addLayout(bottom_row)
        layout.addWidget(info_widget)

        # 卡片阴影
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

    def _load_cover(self):
        if self.game.cover_path and os.path.exists(self.game.cover_path):
            pixmap = QPixmap(self.game.cover_path)
            if not pixmap.isNull():
                # 隐私模式下 R18 游戏封面打马赛克
                # 先 scale 到目标尺寸再 mosaic，效果清晰锐利
                scaled = pixmap.scaled(
                    self.CARD_WIDTH, self.COVER_HEIGHT,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                if self.game.is_r18 and self._privacy_mode:
                    scaled = apply_mosaic(scaled, block_size=9)
                self.cover_label.setPixmap(scaled)
                return

        default = generate_default_cover(self.game.name, self.CARD_WIDTH, self.COVER_HEIGHT)
        # 隐私模式下 R18 默认封面也打马赛克
        if self.game.is_r18 and self._privacy_mode:
            default = apply_mosaic(default, block_size=9)
        self.cover_label.setPixmap(default)

    def _on_play(self):
        self.play_clicked.emit(self.game.id)

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1a2535;
                border: 1px solid #2a4a6a;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                color: #e8edf3;
                padding: 6px 24px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #2a4a6a;
            }
        """)
        delete_action = menu.addAction("删除游戏")
        delete_action.triggered.connect(lambda: self.delete_clicked.emit(self.game.id))
        menu.exec(self.mapToGlobal(pos))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.detail_clicked.emit(self.game.id)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        self._hover = True
        self._overlay.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self._overlay.hide()
        super().leaveEvent(event)

    def update_game(self, game: Game):
        self.game = game
        display_name = mask_name(game.name) if (game.is_r18 and self._privacy_mode) else game.name
        self.title_label.setText(display_name)
        self.title_label.setToolTip(game.name)
        self.time_label.setText(game.format_play_time())
        self._running = game.is_running
        self._update_play_buttons()

    def set_running(self, running: bool):
        self._running = running
        self.game.is_running = running
        self._update_play_buttons()

    def _update_play_buttons(self):
        is_running = self._running
        text = "■" if is_running else "▶"
        tooltip = "关闭游戏" if is_running else "启动游戏"
        prop = str(is_running).lower()

        # 大按钮
        self._big_play_btn.setText(text)
        self._big_play_btn.setProperty("running", prop)
        self._big_play_btn.setToolTip(tooltip)
        self._big_play_btn.style().unpolish(self._big_play_btn)
        self._big_play_btn.style().polish(self._big_play_btn)

        # 小按钮
        self.play_btn.setText(text)
        self.play_btn.setProperty("running", prop)
        self.play_btn.setToolTip(tooltip)
        self.play_btn.style().unpolish(self.play_btn)
        self.play_btn.style().polish(self.play_btn)

        # 提示文字
        self._overlay_hint.setText(tooltip)

    def set_privacy_mode(self, enabled: bool):
        """设置隐私模式，刷新封面和名称显示"""
        self._privacy_mode = enabled
        # 刷新封面
        self._load_cover()
        # 刷新名称
        if self.game.is_r18 and enabled:
            self.title_label.setText(mask_name(self.game.name))
        else:
            self.title_label.setText(self.game.name)
