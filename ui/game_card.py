"""游戏卡片组件 - 精美版"""
import os
from functools import lru_cache

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGraphicsDropShadowEffect, QMenu,
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QVariantAnimation, QTimer, QRectF
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QBrush, QLinearGradient, QCursor, QPainterPath

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


def _load_cover_pixmap(path: str) -> QPixmap:
    """缓存封面文件到 QPixmap，文件变化后自动失效。"""
    try:
        stat = os.stat(path)
        return _load_cover_pixmap_cached(path, stat.st_mtime_ns, stat.st_size)
    except OSError:
        return QPixmap(path)


@lru_cache(maxsize=256)
def _load_cover_pixmap_cached(path: str, mtime_ns: int, size: int) -> QPixmap:
    return QPixmap(path)


def mask_name(name: str) -> str:
    """名称遮蔽：保留首尾各1字，中间用 *** 替代"""
    if len(name) <= 2:
        return name[0] + "***" if name else "***"
    return name[0] + "***" + name[-1]


def fit_cover_pixmap(pixmap: QPixmap, width: int, height: int) -> QPixmap:
    """按封面比例填充并居中裁剪，避免 QLabel 二次拉伸变形。"""
    scaled = pixmap.scaled(
        width, height,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation
    )
    x = max(0, (scaled.width() - width) // 2)
    y = max(0, (scaled.height() - height) // 2)
    return scaled.copy(x, y, width, height)


def round_top_corners(pixmap: QPixmap, radius: int = 9) -> QPixmap:
    """把封面裁成与卡片遮罩一致的上圆角。"""
    if pixmap.isNull() or radius <= 0:
        return pixmap

    result = QPixmap(pixmap.size())
    result.fill(Qt.GlobalColor.transparent)

    path = QPainterPath()
    path.setFillRule(Qt.FillRule.WindingFill)
    rect = QRectF(result.rect())
    path.addRoundedRect(rect, radius, radius)
    path.addRect(QRectF(0, result.height() - radius, radius, radius))
    path.addRect(QRectF(result.width() - radius, result.height() - radius, radius, radius))

    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, pixmap)
    painter.end()
    return result


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
        ((26, 170, 143), (15, 105, 85)),      # 青
        ((72, 175, 235), (40, 110, 160)),    # 亮蓝
        ((175, 115, 200), (110, 60, 135)),   # 淡紫
        ((230, 126, 34), (150, 70, 10)),     # 亮橙
        ((80, 130, 170), (50, 85, 120)),      # 蓝灰
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

    painter.end()
    return pixmap


class GameCard(QWidget):
    """游戏卡片 - 封面、名称、时长、播放按钮"""
    play_clicked = pyqtSignal(str)    # game_id
    detail_clicked = pyqtSignal(str)  # game_id
    edit_clicked = pyqtSignal(str)    # game_id
    delete_clicked = pyqtSignal(str)  # game_id

    CARD_WIDTH = 210
    COVER_HEIGHT = 280
    INFO_HEIGHT = 78

    def __init__(self, game: Game, parent=None):
        super().__init__(parent)
        self.game = game
        self._running = game.is_running
        self._privacy_mode = False
        self.setObjectName("game-card")
        self.setProperty("running", str(self._running).lower())
        self.setProperty("completed", str(self.game.is_completed).lower())
        self.setFixedSize(self.CARD_WIDTH, self.COVER_HEIGHT + self.INFO_HEIGHT)
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
        self._cover_container.setFixedSize(self.CARD_WIDTH, self.COVER_HEIGHT)
        cover_layout = QVBoxLayout(self._cover_container)
        cover_layout.setContentsMargins(0, 0, 0, 0)
        cover_layout.setSpacing(0)

        self.cover_label = QLabel()
        self.cover_label.setFixedSize(self.CARD_WIDTH, self.COVER_HEIGHT)
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setScaledContents(False)
        cover_layout.addWidget(self.cover_label)

        # 悬浮播放遮罩（初始隐藏，鼠标悬停时淡入）
        self._overlay = QWidget(self._cover_container)
        self._overlay.setObjectName("card-cover-overlay")
        self._overlay.setFixedSize(self.CARD_WIDTH, self.COVER_HEIGHT)
        self._overlay.move(0, 0)
        self._overlay.setStyleSheet("background-color: rgba(0,0,0,0); border-radius: 9px 9px 0 0;")
        self._overlay.hide()

        overlay_layout = QVBoxLayout(self._overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setSpacing(14)
        overlay_layout.addStretch(1)

        # 大播放按钮
        self._big_play_btn = QPushButton("▶" if not self._running else "■")
        self._big_play_btn.setObjectName("card-play-overlay-btn")
        self._big_play_btn.setFixedSize(56, 56)
        self._big_play_btn.setProperty("running", str(self._running).lower())
        self._big_play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._big_play_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._big_play_btn.setToolTip("启动游戏" if not self._running else "关闭游戏")
        self._big_play_btn.clicked.connect(self._on_play)
        overlay_layout.addWidget(self._big_play_btn, 0, Qt.AlignmentFlag.AlignHCenter)

        # 提示文字
        self._overlay_hint = QLabel("启动" if not self._running else "关闭")
        self._overlay_hint.setObjectName("card-overlay-hint")
        self._overlay_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._overlay_hint.setFixedWidth(72)
        overlay_layout.addWidget(self._overlay_hint, 0, Qt.AlignmentFlag.AlignHCenter)
        overlay_layout.addStretch(1)

        self._overlay.raise_()
        self._overlay.installEventFilter(self)

        # 遮罩淡入淡出动画
        self._overlay_anim = QVariantAnimation(self)
        self._overlay_anim.setDuration(150)
        self._overlay_anim.valueChanged.connect(self._on_overlay_anim)
        self._overlay_anim.finished.connect(self._on_overlay_anim_done)

        layout.addWidget(self._cover_container)

        # 信息区域
        info_widget = QWidget()
        info_widget.setObjectName("card-info")
        info_widget.setFixedSize(self.CARD_WIDTH, self.INFO_HEIGHT)
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(12, 9, 12, 9)
        info_layout.setSpacing(5)

        # 名称
        display_name = mask_name(self.game.name) if (self.game.is_r18 and self._privacy_mode) else self.game.name
        self.title_label = QLabel(display_name)
        self.title_label.setObjectName("game-title")
        self.title_label.setWordWrap(True)
        self.title_label.setFixedHeight(34)
        self.title_label.setToolTip(self.game.name)
        info_layout.addWidget(self.title_label)

        # 底部行：分类标签 + 私密标签 + 时长
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(6)

        self.category_label = QLabel()
        self.category_label.setObjectName("card-cat-tag")
        bottom_row.addWidget(self.category_label)

        self.r18_label = QLabel("私密")
        self.r18_label.setObjectName("card-r18-tag")
        bottom_row.addWidget(self.r18_label)

        self.completed_label = QLabel("通关")
        self.completed_label.setObjectName("card-completed-tag")
        bottom_row.addWidget(self.completed_label)

        bottom_row.addStretch()
        self.time_label = QLabel(self.game.format_play_time())
        self.time_label.setObjectName("game-time")
        bottom_row.addWidget(self.time_label)

        info_layout.addLayout(bottom_row)
        layout.addWidget(info_widget)
        self._update_meta_labels()

        self._completion_border = QFrame(self)
        self._completion_border.setObjectName("card-completed-border")
        self._completion_border.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._completion_border.setGeometry(self.rect())
        self._completion_border.setVisible(self.game.is_completed)
        self._completion_border.raise_()

        # 卡片阴影
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

    def _load_cover(self):
        if self.game.cover_path and os.path.exists(self.game.cover_path):
            pixmap = _load_cover_pixmap(self.game.cover_path)
            if not pixmap.isNull():
                # 隐私模式下私密内容封面打马赛克
                # 先 scale 到目标尺寸再 mosaic，效果清晰锐利
                scaled = fit_cover_pixmap(pixmap, self.CARD_WIDTH, self.COVER_HEIGHT)
                if self.game.is_r18 and self._privacy_mode:
                    scaled = apply_mosaic(scaled, block_size=9)
                self.cover_label.setPixmap(round_top_corners(scaled))
                return

        default = generate_default_cover(self.game.name, self.CARD_WIDTH, self.COVER_HEIGHT)
        # 隐私模式下私密默认封面也打马赛克
        if self.game.is_r18 and self._privacy_mode:
            default = apply_mosaic(default, block_size=9)
        self.cover_label.setPixmap(round_top_corners(default))

    def _on_play(self):
        self.play_clicked.emit(self.game.id)

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setObjectName("card-context-menu")
        edit_action = menu.addAction("编辑游戏")
        edit_action.triggered.connect(lambda: self.edit_clicked.emit(self.game.id))
        menu.addSeparator()
        delete_action = menu.addAction("删除游戏")
        delete_action.triggered.connect(lambda: self.delete_clicked.emit(self.game.id))
        menu.exec(self.mapToGlobal(pos))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.detail_clicked.emit(self.game.id)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        self._hover = True
        self._fade_overlay(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        QTimer.singleShot(60, self._check_should_hide)
        super().leaveEvent(event)

    def eventFilter(self, obj, event):
        if obj is self._overlay:
            if event.type() == event.Type.Enter:
                self._hover = True
                self._fade_overlay(1.0)
            elif event.type() == event.Type.Leave:
                QTimer.singleShot(60, self._check_should_hide)
        return super().eventFilter(obj, event)

    def _check_should_hide(self):
        if not self.rect().contains(self.mapFromGlobal(QCursor.pos())):
            self._hover = False
            self._fade_overlay(0.0)

    def _fade_overlay(self, target: float):
        self._overlay_anim.stop()
        cur = 1.0 if self._overlay.isVisible() else 0.0
        self._overlay_anim.setStartValue(cur)
        self._overlay_anim.setEndValue(target)
        if target > 0:
            self._overlay.show()
        self._overlay_anim.start()

    def _on_overlay_anim(self, value: float):
        alpha = int(value * 92)
        self._overlay.setStyleSheet(
            f"background-color: rgba(0,0,0,{alpha}); border-radius: 9px 9px 0 0;"
        )

    def _on_overlay_anim_done(self):
        if self._overlay_anim.endValue() == 0.0:
            self._overlay.hide()

    def update_game(self, game: Game):
        self.game = game
        self.setProperty("completed", str(game.is_completed).lower())
        self.style().unpolish(self)
        self.style().polish(self)
        display_name = mask_name(game.name) if (game.is_r18 and self._privacy_mode) else game.name
        self.title_label.setText(display_name)
        self.title_label.setToolTip(game.name)
        self.time_label.setText(game.format_play_time())
        self._update_meta_labels()
        self._running = game.is_running
        self._update_play_buttons()
        self._load_cover()

    def set_running(self, running: bool):
        self._running = running
        self.game.is_running = running
        self._update_play_buttons()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_completion_border"):
            self._completion_border.setGeometry(self.rect())

    def _update_play_buttons(self):
        is_running = self._running
        text = "■" if is_running else "▶"
        tooltip = "关闭游戏" if is_running else "启动游戏"
        prop = str(is_running).lower()

        # 卡片本身运行状态样式
        self.setProperty("running", prop)
        self.style().unpolish(self)
        self.style().polish(self)

        # 大按钮
        self._big_play_btn.setText(text)
        self._big_play_btn.setProperty("running", prop)
        self._big_play_btn.setToolTip(tooltip)
        self._big_play_btn.style().unpolish(self._big_play_btn)
        self._big_play_btn.style().polish(self._big_play_btn)

        # 提示文字
        self._overlay_hint.setText("关闭" if is_running else "启动")

    def _update_meta_labels(self):
        has_category = bool(self.game.category and self.game.category != "其他")
        self.category_label.setVisible(has_category)
        self.category_label.setText(self.game.category if has_category else "")
        self.r18_label.setVisible(self.game.is_r18)
        self.completed_label.setVisible(self.game.is_completed)
        if hasattr(self, "_completion_border"):
            self._completion_border.setVisible(self.game.is_completed)
            self._completion_border.raise_()

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
