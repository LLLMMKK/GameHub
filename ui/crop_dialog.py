"""封面裁剪对话框 - 保持3:4比例裁剪图片"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
)
from PyQt6.QtCore import Qt, QRectF, QSizeF, QPointF, pyqtSignal
from PyQt6.QtGui import (
    QPixmap, QPainter, QPen, QColor, QPainterPath
)
from ui.game_card import fit_cover_pixmap


# 封面宽高比 3:4
COVER_RATIO = 3.0 / 4.0


class CropWidget(QWidget):
    """可交互的图片裁剪区域

    - 拖动裁剪框移动位置
    - 拖动四角缩放裁剪框（保持比例）
    - 外部区域半透明遮罩
    """

    crop_changed = pyqtSignal()

    HANDLE_SIZE = 12

    class _State:
        NONE = 0
        MOVE = 1
        RESIZE_TL = 2
        RESIZE_TR = 3
        RESIZE_BL = 4
        RESIZE_BR = 5

    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self._original = pixmap
        self._state = self._State.NONE
        self._drag_start = None
        self._crop_start_rect = None
        self._crop_rect = QRectF()

        # 计算显示缩放
        max_w, max_h = 640, 520
        scaled = pixmap.scaled(max_w, max_h, Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
        self._display = scaled
        self._scale = scaled.width() / pixmap.width()
        self.setFixedSize(scaled.size())

        # 初始裁剪框：居中、最大可能尺寸
        self._init_crop_rect()
        self.setMouseTracking(True)

    def _init_crop_rect(self):
        img_w = self._display.width()
        img_h = self._display.height()

        # 尝试宽度撑满
        crop_w = img_w
        crop_h = crop_w / COVER_RATIO
        if crop_h > img_h:
            crop_h = img_h
            crop_w = crop_h * COVER_RATIO

        x = (img_w - crop_w) / 2
        y = (img_h - crop_h) / 2
        self._crop_rect = QRectF(x, y, crop_w, crop_h)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制图片
        painter.drawPixmap(0, 0, self._display)

        # 绘制半透明遮罩（裁剪框外部）
        overlay = QColor(0, 0, 0, 160)
        path = QPainterPath()
        path.addRect(QRectF(self.rect()))
        path.addRect(self._crop_rect)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(overlay)
        painter.drawPath(path)

        # 裁剪框边框
        painter.setPen(QPen(QColor(255, 255, 255, 200), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(self._crop_rect)

        # 三分线
        painter.setPen(QPen(QColor(255, 255, 255, 60), 0.5, Qt.PenStyle.DashLine))
        r = self._crop_rect
        for i in (1, 2):
            x = r.left() + r.width() * i / 3
            painter.drawLine(QPointF(x, r.top()), QPointF(x, r.bottom()))
            y = r.top() + r.height() * i / 3
            painter.drawLine(QPointF(r.left(), y), QPointF(r.right(), y))

        # 四角把手
        hs = self.HANDLE_SIZE
        half = hs / 2
        handles = self._get_handle_rects()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 230))
        for h in handles:
            painter.drawRoundedRect(h, 2, 2)

        painter.end()

    def _get_handle_rects(self):
        r = self._crop_rect
        s = self.HANDLE_SIZE
        half = s / 2
        return [
            QRectF(r.left() - half, r.top() - half, s, s),       # TL
            QRectF(r.right() - half, r.top() - half, s, s),      # TR
            QRectF(r.left() - half, r.bottom() - half, s, s),    # BL
            QRectF(r.right() - half, r.bottom() - half, s, s),   # BR
        ]

    def _hit_test(self, pos: QPointF) -> int:
        """检测鼠标点击位置"""
        margin = 6
        handles = self._get_handle_rects()
        states = [self._State.RESIZE_TL, self._State.RESIZE_TR,
                  self._State.RESIZE_BL, self._State.RESIZE_BR]
        for h, st in zip(handles, states):
            if h.adjusted(-margin, -margin, margin, margin).contains(pos):
                return st
        if self._crop_rect.contains(pos):
            return self._State.MOVE
        return self._State.NONE

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._state = self._hit_test(event.position())
            self._drag_start = event.position()
            self._crop_start_rect = QRectF(self._crop_rect)

    def mouseMoveEvent(self, event):
        pos = event.position()

        if self._state == self._State.NONE:
            # 更新光标
            hit = self._hit_test(pos)
            if hit in (self._State.RESIZE_TL, self._State.RESIZE_BR):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif hit in (self._State.RESIZE_TR, self._State.RESIZE_BL):
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            elif hit == self._State.MOVE:
                self.setCursor(Qt.CursorShape.SizeAllCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            return

        delta = pos - self._drag_start

        if self._state == self._State.MOVE:
            self._move_crop(delta)
        elif self._state in (self._State.RESIZE_TL, self._State.RESIZE_TR,
                             self._State.RESIZE_BL, self._State.RESIZE_BR):
            self._resize_crop(delta)

        self.update()
        self.crop_changed.emit()

    def mouseReleaseEvent(self, event):
        self._state = self._State.NONE
        self._drag_start = None
        self._crop_start_rect = None

    def _move_crop(self, delta: QPointF):
        new_rect = self._crop_start_rect.translated(delta)
        # 限制在图片范围内
        if new_rect.left() < 0:
            new_rect.moveLeft(0)
        if new_rect.top() < 0:
            new_rect.moveTop(0)
        if new_rect.right() > self.width():
            new_rect.moveRight(self.width())
        if new_rect.bottom() > self.height():
            new_rect.moveBottom(self.height())
        self._crop_rect = new_rect

    def _resize_crop(self, delta: QPointF):
        cs = self._crop_start_rect
        min_w = 60
        min_h = min_w / COVER_RATIO

        if self._state == self._State.RESIZE_BR:
            # 右下角拖动，左上角固定
            new_w = max(min_w, cs.width() + delta.x())
            new_h = new_w / COVER_RATIO
            # 限制不超出图片
            if cs.left() + new_w > self.width():
                new_w = self.width() - cs.left()
                new_h = new_w / COVER_RATIO
            if cs.top() + new_h > self.height():
                new_h = self.height() - cs.top()
                new_w = new_h * COVER_RATIO
            self._crop_rect = QRectF(cs.topLeft(), QSizeF(new_w, new_h))

        elif self._state == self._State.RESIZE_TL:
            # 左上角拖动，右下角固定
            new_w = max(min_w, cs.width() - delta.x())
            new_h = new_w / COVER_RATIO
            right = cs.right()
            bottom = cs.bottom()
            if right - new_w < 0:
                new_w = right
                new_h = new_w / COVER_RATIO
            if bottom - new_h < 0:
                new_h = bottom
                new_w = new_h * COVER_RATIO
            self._crop_rect = QRectF(QPointF(right - new_w, bottom - new_h), QSizeF(new_w, new_h))

        elif self._state == self._State.RESIZE_TR:
            # 右上角拖动，左下角固定
            new_w = max(min_w, cs.width() + delta.x())
            new_h = new_w / COVER_RATIO
            left = cs.left()
            bottom = cs.bottom()
            if left + new_w > self.width():
                new_w = self.width() - left
                new_h = new_w / COVER_RATIO
            if bottom - new_h < 0:
                new_h = bottom
                new_w = new_h * COVER_RATIO
            self._crop_rect = QRectF(QPointF(left, bottom - new_h), QSizeF(new_w, new_h))

        elif self._state == self._State.RESIZE_BL:
            # 左下角拖动，右上角固定
            new_w = max(min_w, cs.width() - delta.x())
            new_h = new_w / COVER_RATIO
            right = cs.right()
            top = cs.top()
            if right - new_w < 0:
                new_w = right
                new_h = new_w / COVER_RATIO
            if top + new_h > self.height():
                new_h = self.height() - top
                new_w = new_h * COVER_RATIO
            self._crop_rect = QRectF(QPointF(right - new_w, top), QSizeF(new_w, new_h))

    def get_cropped_pixmap(self) -> QPixmap:
        """将裁剪框区域映射回原图坐标并裁剪"""
        orig_x = int(self._crop_rect.x() / self._scale)
        orig_y = int(self._crop_rect.y() / self._scale)
        orig_w = int(self._crop_rect.width() / self._scale)
        orig_h = int(self._crop_rect.height() / self._scale)

        # 安全边界
        orig_w = max(1, min(orig_w, self._original.width() - orig_x))
        orig_h = max(1, min(orig_h, self._original.height() - orig_y))

        return self._original.copy(orig_x, orig_y, orig_w, orig_h)


class CoverCropDialog(QDialog):
    """封面裁剪对话框"""

    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self._result = None
        self._setup_ui(pixmap)

    def _setup_ui(self, pixmap: QPixmap):
        self.setWindowTitle("裁剪封面")
        self.setMinimumWidth(700)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 20)

        # 提示
        hint = QLabel("拖动裁剪框移动位置，拖动四角调整大小（自动保持3:4封面比例）")
        hint.setObjectName("dialog-hint")
        layout.addWidget(hint)

        # 裁剪区域
        self._crop_widget = CropWidget(pixmap)
        self._crop_widget.crop_changed.connect(self._update_preview)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(self._crop_widget)
        row.addStretch()
        layout.addLayout(row)

        layout.addSpacing(8)

        # 预览行
        preview_row = QHBoxLayout()
        preview_row.setSpacing(16)

        preview_label = QLabel("裁剪预览:")
        preview_label.setObjectName("dialog-muted")
        preview_row.addWidget(preview_label)

        self._preview = QLabel()
        self._preview.setFixedSize(90, 120)
        self._preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview.setObjectName("crop-preview-box")
        preview_row.addWidget(self._preview)

        preview_row.addStretch()

        size_label = QLabel()
        size_label.setObjectName("dialog-subtle")
        self._size_label = size_label
        preview_row.addWidget(size_label)

        layout.addLayout(preview_row)

        # 初始化预览
        self._update_preview()

        # 按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("secondary-btn")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        confirm_btn = QPushButton("确认裁剪")
        confirm_btn.setObjectName("primary-btn")
        confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm_btn.clicked.connect(self._confirm)
        btn_row.addWidget(confirm_btn)

        layout.addLayout(btn_row)

    def _update_preview(self):
        cropped = self._crop_widget.get_cropped_pixmap()
        self._preview.setPixmap(fit_cover_pixmap(cropped, 90, 120))
        self._size_label.setText(f"{cropped.width()} x {cropped.height()} px")

    def _confirm(self):
        self._result = self._crop_widget.get_cropped_pixmap()
        self.accept()

    def get_cropped_pixmap(self) -> QPixmap | None:
        return self._result
