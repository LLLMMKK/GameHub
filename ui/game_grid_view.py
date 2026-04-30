"""High-performance game grid based on QListView + painted delegate."""

import os

from PyQt6.QtCore import (
    QAbstractListModel, QEvent, QModelIndex, QRect, QRectF, QSize, Qt,
    QVariantAnimation, pyqtSignal
)
from PyQt6.QtGui import (
    QBrush, QColor, QCursor, QFont, QFontMetrics, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
)
from PyQt6.QtWidgets import QAbstractItemView, QListView, QMenu, QStyledItemDelegate, QStyle

from core.game_model import Game
from ui.game_card import (
    _load_cover_pixmap, apply_mosaic, fit_cover_pixmap, generate_default_cover, mask_name
)
from ui.styles import _COLORS


def _color(value: str, fallback: str = "#000000") -> QColor:
    """Parse theme colors including simple rgba(...) strings used by QSS tokens."""
    if not value:
        return QColor(fallback)
    value = value.strip()
    if value.startswith("rgba(") and value.endswith(")"):
        parts = [p.strip() for p in value[5:-1].split(",")]
        if len(parts) == 4:
            return QColor(int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]))
    return QColor(value)


class GameListModel(QAbstractListModel):
    GameRole = int(Qt.ItemDataRole.UserRole) + 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._games: list[Game] = []

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._games)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() < 0 or index.row() >= len(self._games):
            return None
        game = self._games[index.row()]
        if role == self.GameRole:
            return game
        if role == Qt.ItemDataRole.DisplayRole:
            return game.name
        return None

    def set_games(self, games: list[Game]):
        self.beginResetModel()
        self._games = list(games)
        self.endResetModel()

    def game_at(self, row: int) -> Game | None:
        if 0 <= row < len(self._games):
            return self._games[row]
        return None

    def refresh_game(self, game_id: str):
        for row, game in enumerate(self._games):
            if game.id == game_id:
                index = self.index(row, 0)
                self.dataChanged.emit(index, index, [self.GameRole, Qt.ItemDataRole.DisplayRole])
                return


class GameCardDelegate(QStyledItemDelegate):
    CARD_WIDTH = 210
    COVER_HEIGHT = 280
    INFO_HEIGHT = 78
    CARD_HEIGHT = COVER_HEIGHT + INFO_HEIGHT
    CELL_WIDTH = 226
    CELL_HEIGHT = 390

    def __init__(self, parent=None):
        super().__init__(parent)
        self._privacy_mode = False
        self._theme_name = "暗夜"
        self._colors = _COLORS.get(self._theme_name, _COLORS["暗夜"])
        self._cover_cache: dict[tuple, object] = {}
        self._hover_row = -1
        self._fade_row = -1
        self._hover_opacity = 0.0

    def sizeHint(self, option, index) -> QSize:
        return QSize(self.CELL_WIDTH, self.CELL_HEIGHT)

    def set_privacy_mode(self, enabled: bool):
        if self._privacy_mode != enabled:
            self._privacy_mode = enabled
            self._cover_cache.clear()

    def set_theme(self, theme_name: str):
        self._theme_name = theme_name
        self._colors = _COLORS.get(theme_name, _COLORS["暗夜"])

    def clear_cache(self):
        self._cover_cache.clear()

    def set_hover_state(self, row: int, opacity: float):
        self._hover_row = row
        self._hover_opacity = max(0.0, min(1.0, opacity))

    def card_rect(self, cell_rect: QRect) -> QRect:
        x = cell_rect.x() + max(0, (cell_rect.width() - self.CARD_WIDTH) // 2)
        y = cell_rect.y() + max(0, (cell_rect.height() - self.CARD_HEIGHT) // 2)
        return QRect(x, y, self.CARD_WIDTH, self.CARD_HEIGHT)

    def _top_rounded_path(self, rect: QRect, radius: int) -> QPainterPath:
        r = QRectF(rect)
        path = QPainterPath()
        path.moveTo(r.left() + radius, r.top())
        path.lineTo(r.right() - radius, r.top())
        path.quadTo(r.right(), r.top(), r.right(), r.top() + radius)
        path.lineTo(r.right(), r.bottom())
        path.lineTo(r.left(), r.bottom())
        path.lineTo(r.left(), r.top() + radius)
        path.quadTo(r.left(), r.top(), r.left() + radius, r.top())
        path.closeSubpath()
        return path

    def _is_cursor_over_card(self, index: QModelIndex) -> bool:
        view = self.parent()
        if not view or not hasattr(view, "viewport") or not hasattr(view, "indexAt"):
            return False
        viewport = view.viewport()
        pos = viewport.mapFromGlobal(QCursor.pos())
        if not viewport.rect().contains(pos):
            return False
        hovered_index = view.indexAt(pos)
        if not hovered_index.isValid() or hovered_index.row() != index.row():
            return False
        return self.card_rect(view.visualRect(index)).contains(pos)

    def paint(self, painter: QPainter, option, index: QModelIndex):
        game = index.data(GameListModel.GameRole)
        if not game:
            return

        painter.save()
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            cursor_hovered = self._is_cursor_over_card(index)
            state_hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
            tracked_hovered = index.row() == self._hover_row and self._hover_opacity > 0.0
            hovered = cursor_hovered or state_hovered or tracked_hovered
            hover_opacity = 1.0 if cursor_hovered or state_hovered else self._hover_opacity
            selected = bool(option.state & QStyle.StateFlag.State_Selected)
            card = self.card_rect(option.rect)
            cover = QRect(card.x(), card.y(), self.CARD_WIDTH, self.COVER_HEIGHT)
            info = QRect(card.x(), card.y() + self.COVER_HEIGHT, self.CARD_WIDTH, self.INFO_HEIGHT)

            self._draw_shadow(painter, card, hover_opacity if hovered else 0.0)
            self._draw_card_frame(painter, card, game, hovered, selected)
            self._draw_cover(painter, cover, game, hover_opacity if hovered else 0.0)
            self._draw_info(painter, info, game)
            if game.is_completed:
                painter.setPen(QPen(_color(self._colors["completed_border"]), 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(QRectF(card).adjusted(1, 1, -1, -1), 8, 8)
        except Exception as exc:
            print(f"GameCardDelegate paint error: {exc}")
        finally:
            painter.restore()

    def _draw_shadow(self, painter: QPainter, rect: QRect, hover_opacity: float):
        painter.setPen(Qt.PenStyle.NoPen)
        layers = (
            (1, 2, 18 + int(8 * hover_opacity)),
            (2, 4, 13 + int(7 * hover_opacity)),
            (3, 7, 8 + int(6 * hover_opacity)),
            (4, 10, 5 + int(4 * hover_opacity)),
        )
        for grow, offset, alpha in layers:
            shadow_rect = QRectF(rect).translated(0, offset).adjusted(-grow, -grow, grow, grow)
            painter.setBrush(QColor(0, 0, 0, alpha))
            painter.drawRoundedRect(shadow_rect, 10 + grow, 10 + grow)


    def _draw_card_frame(self, painter: QPainter, rect: QRect, game: Game, hovered: bool, selected: bool):
        bg = _color(self._colors["bg_card"])
        border_key = "border"
        if game.is_running:
            bg = _color(self._colors.get("bg_running", self._colors["bg_card"]))
            border_key = "green_hover" if hovered else "green_border"
        if game.is_completed:
            border_key = "completed_border_hover" if hovered else "completed_border"
        if selected:
            border_key = "accent"
        border = _color(self._colors["border_btn_secondary"] if hovered else self._colors[border_key])
        painter.setPen(QPen(border, 1))
        painter.setBrush(bg)
        painter.drawRoundedRect(QRectF(rect), 8, 8)

    def _draw_cover(self, painter: QPainter, rect: QRect, game: Game, hover_opacity: float = 0.0):
        pixmap = self._cover_for_game(game)
        if hover_opacity > 0.0:
            pixmap = self._hover_cover(pixmap, hover_opacity)

        painter.save()
        painter.setClipPath(self._top_rounded_path(rect, 9))
        painter.drawPixmap(rect, pixmap)
        painter.restore()

    def _cover_for_game(self, game: Game):
        cover_sig = None
        if game.cover_path:
            try:
                stat = os.stat(game.cover_path)
                cover_sig = (game.cover_path, stat.st_mtime_ns, stat.st_size)
            except OSError:
                cover_sig = (game.cover_path, None, None)

        key = (game.id, game.name, cover_sig, game.is_r18, self._privacy_mode)
        cached = self._cover_cache.get(key)
        if cached is not None:
            return cached

        pixmap = None
        if game.cover_path and cover_sig and cover_sig[1] is not None:
            loaded = _load_cover_pixmap(game.cover_path)
            if not loaded.isNull():
                pixmap = fit_cover_pixmap(loaded, self.CARD_WIDTH, self.COVER_HEIGHT)

        if pixmap is None:
            pixmap = generate_default_cover(game.name, self.CARD_WIDTH, self.COVER_HEIGHT)

        if game.is_r18 and self._privacy_mode:
            pixmap = apply_mosaic(pixmap, block_size=9)

        if len(self._cover_cache) > 384:
            self._cover_cache.clear()
        self._cover_cache[key] = pixmap
        return pixmap

    def _hover_cover(self, source: QPixmap, opacity: float) -> QPixmap:
        pixmap = QPixmap(source)
        painter = QPainter(pixmap)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)

            shade = QLinearGradient(0, 0, 0, pixmap.height())
            shade.setColorAt(0.0, QColor(255, 255, 255, int(18 * opacity)))
            shade.setColorAt(0.25, QColor(0, 0, 0, int(54 * opacity)))
            shade.setColorAt(1.0, QColor(0, 0, 0, int(150 * opacity)))
            painter.setBrush(QBrush(shade))
            painter.drawRect(pixmap.rect())

            side = QLinearGradient(0, 0, pixmap.width(), 0)
            side.setColorAt(0.0, QColor(255, 255, 255, int(32 * opacity)))
            side.setColorAt(0.55, QColor(255, 255, 255, 0))
            side.setColorAt(1.0, QColor(0, 0, 0, int(38 * opacity)))
            painter.setBrush(QBrush(side))
            painter.drawRect(pixmap.rect())
        finally:
            painter.end()
        return pixmap

    def _draw_info(self, painter: QPainter, rect: QRect, game: Game):
        painter.fillRect(rect, _color(self._colors["bg_card"]))
        painter.setPen(QPen(_color(self._colors["border"]), 1))
        painter.drawLine(rect.topLeft(), rect.topRight())

        display_name = mask_name(game.name) if (game.is_r18 and self._privacy_mode) else game.name
        title_rect = QRect(rect.x() + 12, rect.y() + 9, rect.width() - 24, 34)
        painter.setPen(_color(self._colors["text_primary"]))
        font = QFont("Microsoft YaHei", 10)
        font.setBold(True)
        painter.setFont(font)
        self._draw_two_line_text(painter, title_rect, display_name)

        x = rect.x() + 12
        y = rect.y() + 50
        if game.category and game.category != "其他":
            x = self._draw_pill(
                painter, x, y, game.category,
                _color(self._colors["accent"]),
                _color(self._colors["bg_overlay"]),
                _color(self._colors["border_btn_secondary"])
            )
        if game.is_r18:
            x = self._draw_pill(
                painter, x, y, "私密",
                _color(self._colors["private_tag_text"]),
                _color(self._colors["private_tag_bg"]),
                _color(self._colors["private_tag_border"])
            )
        if game.is_completed:
            self._draw_pill(
                painter, x, y, "通关",
                _color(self._colors["completed_text"]),
                _color(self._colors["completed_bg"]),
                _color(self._colors["completed_tag_border"])
            )

        time = game.format_play_time()
        painter.setPen(_color(self._colors["text_muted"]))
        painter.setFont(QFont("Microsoft YaHei", 9))
        metrics = QFontMetrics(painter.font())
        time_width = metrics.horizontalAdvance(time)
        painter.drawText(
            QRect(rect.right() - time_width - 12, y - 1, time_width + 2, 18),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            time
        )

    def _draw_two_line_text(self, painter: QPainter, rect: QRect, text: str):
        metrics = QFontMetrics(painter.font())
        words = list(text)
        lines: list[str] = []
        current = ""
        for ch in words:
            candidate = current + ch
            if metrics.horizontalAdvance(candidate) <= rect.width() or not current:
                current = candidate
            else:
                lines.append(current)
                current = ch
                if len(lines) == 1:
                    break
        if current and len(lines) < 2:
            lines.append(current)
        if len(lines) == 2 and len("".join(lines)) < len(text):
            lines[1] = metrics.elidedText(lines[1] + text[len("".join(lines)):], Qt.TextElideMode.ElideRight, rect.width())
        painter.drawText(rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, "\n".join(lines[:2]))

    def _draw_pill(self, painter: QPainter, x: int, y: int, text: str, fg: QColor, bg: QColor, border: QColor) -> int:
        font = QFont("Microsoft YaHei", 8)
        font.setBold(True)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        width = min(metrics.horizontalAdvance(text) + 12, 72)
        pill = QRect(x, y, width, 18)
        painter.setPen(QPen(border, 1))
        painter.setBrush(bg)
        painter.drawRoundedRect(QRectF(pill), 4, 4)
        painter.setPen(fg)
        painter.drawText(pill.adjusted(6, 0, -6, 0), Qt.AlignmentFlag.AlignCenter, metrics.elidedText(text, Qt.TextElideMode.ElideRight, width - 12))
        return x + width + 6


class GameGridView(QListView):
    detail_clicked = pyqtSignal(str)
    edit_clicked = pyqtSignal(str)
    delete_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = GameListModel(self)
        self._delegate = GameCardDelegate(self)
        self._hover_row = -1
        self._hover_opacity = 0.0
        self._hover_anim = QVariantAnimation(self)
        self._hover_anim.setDuration(150)
        self._hover_anim.valueChanged.connect(self._on_hover_anim)
        self.setModel(self._model)
        self.setItemDelegate(self._delegate)
        self.setObjectName("game-grid-view")
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setFlow(QListView.Flow.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setMovement(QListView.Movement.Static)
        self.setUniformItemSizes(True)
        self.setSpacing(12)
        self.setGridSize(QSize(GameCardDelegate.CELL_WIDTH, GameCardDelegate.CELL_HEIGHT))
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.viewport().setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.viewport().installEventFilter(self)
        self.entered.connect(self._on_index_entered)
        self.setToolTip("")
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.verticalScrollBar().setSingleStep(24)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def set_games(self, games: list[Game]):
        self._delegate.clear_cache()
        self._model.set_games(games)
        self.scrollToTop()

    def set_privacy_mode(self, enabled: bool):
        self._delegate.set_privacy_mode(enabled)
        self.viewport().update()

    def set_theme(self, theme_name: str):
        self._delegate.set_theme(theme_name)
        self.viewport().update()

    def refresh_game(self, game_id: str):
        self._delegate.clear_cache()
        self._model.refresh_game(game_id)
        self.viewport().update()

    def mouseMoveEvent(self, event):
        row = self._card_row_at(event.pos())
        self._set_hover_row(row)
        self.setCursor(Qt.CursorShape.PointingHandCursor if row >= 0 else Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._set_hover_row(-1)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().leaveEvent(event)

    def viewportEvent(self, event):
        if event.type() == QEvent.Type.MouseMove:
            pos = event.position().toPoint()
            row = self._card_row_at(pos)
            self._set_hover_row(row)
            self.viewport().setCursor(Qt.CursorShape.PointingHandCursor if row >= 0 else Qt.CursorShape.ArrowCursor)
            self.viewport().update()
        elif event.type() == QEvent.Type.HoverMove:
            pos = event.position().toPoint()
            row = self._card_row_at(pos)
            self._set_hover_row(row)
            self.viewport().setCursor(Qt.CursorShape.PointingHandCursor if row >= 0 else Qt.CursorShape.ArrowCursor)
            self.viewport().update()
        elif event.type() == QEvent.Type.Leave:
            self._set_hover_row(-1)
            self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
            self.viewport().update()
        return super().viewportEvent(event)

    def eventFilter(self, obj, event):
        if obj is self.viewport():
            if event.type() == QEvent.Type.MouseMove:
                pos = event.position().toPoint()
                row = self._card_row_at(pos)
                self._set_hover_row(row)
                self.viewport().setCursor(Qt.CursorShape.PointingHandCursor if row >= 0 else Qt.CursorShape.ArrowCursor)
                self.viewport().update()
            elif event.type() == QEvent.Type.HoverMove:
                pos = event.position().toPoint()
                row = self._card_row_at(pos)
                self._set_hover_row(row)
                self.viewport().setCursor(Qt.CursorShape.PointingHandCursor if row >= 0 else Qt.CursorShape.ArrowCursor)
                self.viewport().update()
            elif event.type() == QEvent.Type.Leave:
                self._set_hover_row(-1)
                self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
                self.viewport().update()
        return super().eventFilter(obj, event)

    def _on_index_entered(self, index: QModelIndex):
        if index.isValid():
            self._set_hover_row(index.row())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            index = self.indexAt(event.pos())
            row = self._card_row_at(event.pos())
            game = self._model.game_at(row) if row >= 0 and index.isValid() and index.row() == row else None
            if game:
                self.detail_clicked.emit(game.id)
                event.accept()
                return
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        bar = self.verticalScrollBar()
        pixel_delta = event.pixelDelta().y()
        angle_delta = event.angleDelta().y()
        if pixel_delta:
            distance = -int(pixel_delta * 0.55)
        elif angle_delta:
            distance = -int(angle_delta / 120 * 72)
        else:
            super().wheelEvent(event)
            return

        bar.setValue(bar.value() + distance)
        event.accept()

    def _card_row_at(self, pos) -> int:
        index = self.indexAt(pos)
        if not index.isValid():
            return -1
        if not self._delegate.card_rect(self.visualRect(index)).contains(pos):
            return -1
        return index.row()

    def _set_hover_row(self, row: int):
        if row == self._hover_row:
            return
        old_row = self._hover_row
        self._hover_row = row
        self._hover_anim.stop()
        if row >= 0:
            self._fade_row = row
            self._hover_opacity = max(self._hover_opacity, 0.28)
            self._hover_anim.setStartValue(self._hover_opacity)
            self._hover_anim.setEndValue(1.0)
        else:
            self._fade_row = old_row
            self._hover_anim.setStartValue(self._hover_opacity)
            self._hover_anim.setEndValue(0.0)
        self._delegate.set_hover_state(row if row >= 0 else old_row, self._hover_opacity)
        self._update_rows(old_row, row)
        self._hover_anim.start()

    def _on_hover_anim(self, value: float):
        self._hover_opacity = float(value)
        paint_row = self._hover_row if self._hover_row >= 0 else self._fade_row
        self._delegate.set_hover_state(paint_row, self._hover_opacity)
        self._update_rows(paint_row)
        if self._hover_opacity <= 0.0 and self._hover_row < 0:
            self._fade_row = -1
            self._delegate.set_hover_state(-1, 0.0)
            self.viewport().update()

    def _update_rows(self, *rows: int):
        for row in rows:
            if row < 0:
                continue
            index = self._model.index(row, 0)
            if index.isValid():
                self.viewport().update(self.visualRect(index).adjusted(-12, -12, 12, 18))

    def _show_context_menu(self, pos):
        row = self._card_row_at(pos)
        game = self._model.game_at(row) if row >= 0 else None
        if not game:
            return
        menu = QMenu(self)
        menu.setObjectName("card-context-menu")
        edit_action = menu.addAction("编辑游戏")
        edit_action.triggered.connect(lambda: self.edit_clicked.emit(game.id))
        menu.addSeparator()
        delete_action = menu.addAction("删除游戏")
        delete_action.triggered.connect(lambda: self.delete_clicked.emit(game.id))
        menu.exec(self.mapToGlobal(pos))
