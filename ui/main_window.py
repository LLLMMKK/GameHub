"""主窗口 - 整合侧边栏、游戏卡片网格、详情面板"""
import os
import traceback

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QScrollArea, QGridLayout,
    QFrame, QFileDialog, QMessageBox, QComboBox,
    QGraphicsOpacityEffect, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRectF, QEvent
from PyQt6.QtGui import QShortcut, QKeySequence, QFont, QPainter, QPen, QColor

from core.game_model import GameDataStore, Game
from core.game_launcher import GameLauncher
from core.play_tracker import PlayTracker
from core.game_scanner import GameScanner
from ui.sidebar import Sidebar
from ui.game_card import GameCard
from ui.game_detail import GameDetailPage
from ui.add_game_dialog import AddGameDialog
from ui.settings_dialog import SettingsDialog
from ui.scan_result_dialog import ScanResultDialog
from utils.file_utils import get_exe_name


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GameHub - 游戏管理器")
        self.setMinimumSize(800, 500)
        self.resize(1200, 800)

        # 核心模块
        self.store = GameDataStore()
        self.launcher = GameLauncher(self)
        self.tracker = PlayTracker(self.store)
        self.scanner = GameScanner()

        # 当前状态
        self._current_category = "全部"
        self._search_query = ""
        self._sort_mode = self.store.sort_mode
        self._selected_game_id = None
        self._cards: dict[str, "GameCard"] = {}  # game_id -> GameCard 快速查找
        self._last_cols = 0  # 上次列数，避免列数不变时重建卡片

        # 边缘拖拽缩放状态
        self._resize_edge = None         # Qt.Edge | None
        self._resize_start_geo = None    # QRect
        self._resize_start_pos = None    # QPoint (global)
        self._override_cursor_active = False

        # 防抖：resize 时延迟刷新卡片，避免拖动卡顿
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(50)
        self._resize_timer.timeout.connect(self._refresh_cards)

        self._setup_ui()
        self._apply_frameless_mode(self.store.frameless_mode)
        self._connect_signals()
        self._setup_shortcuts()
        self._setup_splash_overlay()
        self._refresh()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self._main_layout = main_layout

        # 侧边栏
        self.sidebar = Sidebar()
        main_layout.addWidget(self.sidebar)

        # 中间内容区
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 顶部工具栏
        toolbar = self._create_toolbar()
        content_layout.addWidget(toolbar)

        # 游戏卡片网格
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.grid_container = QWidget()
        self.grid_layout = QVBoxLayout(self.grid_container)
        self.grid_layout.setContentsMargins(20, 16, 8, 16)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 卡片网格
        self.card_grid = QGridLayout()
        self.card_grid.setSpacing(16)
        self.grid_layout.addLayout(self.card_grid)

        # 空状态提示
        self.empty_label = QLabel("还没有游戏\n点击上方「添加游戏」开始吧")
        self.empty_label.setObjectName("empty-hint")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grid_layout.addWidget(self.empty_label)
        self.empty_label.hide()

        self.scroll_area.setWidget(self.grid_container)
        content_layout.addWidget(self.scroll_area, 1)

        main_layout.addWidget(content, 1)

        # 详情页面（默认隐藏，替换卡片网格显示）
        self.detail_page = GameDetailPage()
        self.detail_page.hide()
        content_layout.addWidget(self.detail_page, 1)

    class _WinControlButton(QPushButton):
        """手绘窗口控制按钮，避免 Unicode 字符在不同字体下对齐不一致"""

        def __init__(self, icon_type: str, parent=None):
            super().__init__(parent)
            self._icon_type = icon_type  # 'min', 'max', 'close'
            self._is_maximized = False
            self.setFixedSize(40, 30)
            self.setCursor(Qt.CursorShape.PointingHandCursor)

        def set_maximized_state(self, state: bool):
            self._is_maximized = state
            self.update()

        def paintEvent(self, event):
            super().paintEvent(event)
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)

            # 用 QSS 中 color 属性对应的 palette 颜色
            icon_color = self.palette().color(self.foregroundRole())
            pen = QPen(icon_color, 1.2)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)

            w, h = self.width(), self.height()
            cx, cy = w / 2, h / 2

            if self._icon_type == 'min':
                # 居中短横线
                y = int(cy)
                x0, x1 = int(cx - 5), int(cx + 5)
                p.drawLine(x0, y, x1, y)
                p.drawLine(x0, y + 1, x1, y + 1)

            elif self._icon_type == 'max':
                if self._is_maximized:
                    # 还原图标：前后两个错位方框
                    s, ox, oy = 7, 2, -2
                    back = QRectF(cx - s - ox, cy - s - oy, s * 2, s * 2)
                    front = QRectF(cx - s + ox, cy - s + oy, s * 2, s * 2)
                    # 前面的框用父窗口背景色填充，盖住后面框的内部
                    parent_bg = self.window().palette().color(
                        self.window().backgroundRole())
                    p.setBrush(parent_bg)
                    p.drawRect(front)
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    p.drawRect(front)
                    p.drawRect(back)
                else:
                    # 最大化：单个空心方框
                    s = 7
                    p.drawRect(QRectF(cx - s, cy - s, s * 2, s * 2))

            elif self._icon_type == 'close':
                # X 形
                d = 5
                p.drawLine(int(cx - d), int(cy - d), int(cx + d), int(cy + d))
                p.drawLine(int(cx - d), int(cy + d), int(cx + d), int(cy - d))
                p.drawLine(int(cx - d), int(cy - d + 1), int(cx + d - 1), int(cy + d))
                p.drawLine(int(cx - d + 1), int(cy + d), int(cx + d), int(cy - d + 1))

            p.end()

    class _FramelessToolbar(QWidget):
        """支持 frameless 模式拖拽的工具栏"""
        def __init__(self, main_window):
            super().__init__()
            self._main = main_window

        def mousePressEvent(self, event):
            if event.button() == Qt.MouseButton.LeftButton and self._main.store.frameless_mode:
                self.window().windowHandle().startSystemMove()
            super().mousePressEvent(event)

        def mouseDoubleClickEvent(self, event):
            if self._main.store.frameless_mode:
                win = self.window()
                if win.isMaximized():
                    win.showNormal()
                else:
                    win.showMaximized()
            super().mouseDoubleClickEvent(event)

    def _create_toolbar(self) -> QWidget:
        toolbar = MainWindow._FramelessToolbar(self)
        toolbar.setObjectName("toolbar")
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(24, 10, 24, 10)

        # 当前分类标题
        self.category_title = QLabel("全部游戏")
        self.category_title.setObjectName("category-title")
        layout.addWidget(self.category_title)

        # 游戏数量标记
        self.game_count_label = QLabel("")
        self.game_count_label.setObjectName("game-count-badge")
        layout.addWidget(self.game_count_label)

        layout.addStretch()

        # 排序选择
        sort_label = QLabel("排序:")
        sort_label.setObjectName("sort-label")
        layout.addWidget(sort_label)

        self.sort_combo = QComboBox()
        self.sort_combo.setObjectName("sort-combo")
        self.sort_combo.addItems(["名称", "游玩时长", "最近游玩", "添加时间"])
        modes = ["name", "play_time", "last_played", "added_time"]
        self.sort_combo.setCurrentIndex(modes.index(self._sort_mode) if self._sort_mode in modes else 0)
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        layout.addWidget(self.sort_combo)

        layout.addSpacing(12)

        # 扫描按钮
        scan_btn = QPushButton("扫描目录")
        scan_btn.setObjectName("toolbar-btn")
        scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        scan_btn.setToolTip("扫描本地目录自动添加游戏")
        scan_btn.clicked.connect(self._scan_directory)
        layout.addWidget(scan_btn)

        layout.addSpacing(8)

        # 手动选择按钮
        manual_btn = QPushButton("手动选择")
        manual_btn.setObjectName("toolbar-btn")
        manual_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        manual_btn.setToolTip("手动选择多个游戏可执行文件")
        manual_btn.clicked.connect(self._manual_select)
        layout.addWidget(manual_btn)

        layout.addSpacing(8)

        # 添加游戏按钮
        add_btn = QPushButton("+ 添加游戏")
        add_btn.setObjectName("add-game-btn")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setToolTip("手动添加一个游戏")
        add_btn.clicked.connect(self._add_game)
        layout.addWidget(add_btn)

        layout.addSpacing(8)

        # 设置按钮
        settings_btn = QPushButton("设置")
        settings_btn.setObjectName("toolbar-btn")
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.clicked.connect(self._show_settings)
        layout.addWidget(settings_btn)

        layout.addSpacing(12)

        # 窗口控制按钮（仅 frameless 模式显示）
        self._btn_minimize = MainWindow._WinControlButton('min')
        self._btn_minimize.setObjectName("win-control-btn")
        self._btn_minimize.clicked.connect(self.showMinimized)
        self._btn_minimize.hide()
        layout.addWidget(self._btn_minimize)

        self._btn_maximize = MainWindow._WinControlButton('max')
        self._btn_maximize.setObjectName("win-control-btn")
        self._btn_maximize.clicked.connect(self._toggle_maximize)
        self._btn_maximize.hide()
        layout.addWidget(self._btn_maximize)

        self._btn_close = MainWindow._WinControlButton('close')
        self._btn_close.setObjectName("win-close-btn")
        self._btn_close.clicked.connect(self.close)
        self._btn_close.hide()
        layout.addWidget(self._btn_close)

        self.toolbar_widget = toolbar
        return toolbar

    def _connect_signals(self):
        self.sidebar.category_changed.connect(self._on_category_changed)
        self.sidebar.search_changed.connect(self._on_search_changed)
        self.launcher.game_started.connect(self._on_game_started)
        self.launcher.game_exited.connect(self._on_game_exited)
        self.detail_page.play_clicked.connect(self._toggle_game)
        self.detail_page.edit_clicked.connect(self._edit_game)
        self.detail_page.delete_clicked.connect(self._delete_game)
        self.detail_page.back_clicked.connect(self._close_detail)
        self.detail_page.cover_changed.connect(self._on_cover_changed)
        self.detail_page.desc_changed.connect(self._on_desc_changed)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self._shortcut_search)
        QShortcut(QKeySequence(Qt.Key.Key_Delete), self, activated=self._shortcut_delete)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, activated=self._shortcut_escape)

    def _shortcut_search(self):
        self.sidebar.search_box.setFocus()
        self.sidebar.search_box.selectAll()

    def _shortcut_delete(self):
        if self._selected_game_id and self.detail_page.isVisible():
            self._delete_game(self._selected_game_id)

    def _shortcut_escape(self):
        if self.detail_page.isVisible():
            self._close_detail()

    def _refresh(self):
        """刷新界面"""
        # 更新侧边栏
        counts = {"全部": len(self.store.games)}
        recent = [g for g in self.store.games if g.last_played]
        counts["最近游玩"] = len(recent)
        for game in self.store.games:
            counts[game.category] = counts.get(game.category, 0) + 1

        # 只在分类列表变化时重建按钮，平时仅更新计数
        current_cats = [b.category_name for b in self.sidebar._buttons]
        if current_cats != self.store.categories:
            self.sidebar.set_categories(self.store.categories, counts)
        else:
            self.sidebar.update_counts(counts)

        # 刷新卡片
        self._refresh_cards(force=True)

    def _refresh_cards(self, force=False):
        """刷新游戏卡片 — force=True 时跳过列数缓存检查"""
        cols = self._calc_columns()
        if not force and cols == self._last_cols and self.card_grid.count() > 0:
            return
        self._last_cols = cols

        # 清除旧卡片
        self._cards.clear()
        while self.card_grid.count():
            item = self.card_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 获取要显示的游戏
        games = self._get_filtered_games()

        # 更新标题
        if self._search_query:
            self.category_title.setText(f"搜索: {self._search_query}")
        elif self._current_category == "全部":
            self.category_title.setText("全部游戏")
        elif self._current_category == "最近游玩":
            self.category_title.setText("最近游玩")
        else:
            self.category_title.setText(self._current_category)

        self.game_count_label.setText(f"({len(games)})")

        # 空状态
        if not games:
            self.empty_label.show()
            return

        self.empty_label.hide()

        for i, game in enumerate(games):
            card = GameCard(game)
            card.set_privacy_mode(self.store.privacy_mode)
            card.play_clicked.connect(self._toggle_game)
            card.detail_clicked.connect(self._show_detail)
            card.edit_clicked.connect(self._edit_game)
            card.delete_clicked.connect(self._delete_game)
            row, col = divmod(i, cols)
            self.card_grid.addWidget(card, row, col)
            self._cards[game.id] = card

    def _calc_columns(self):
        if self.isVisible():
            viewport_width = self.scroll_area.viewport().width()
        else:
            viewport_width = max(800, self.width() - 217)
        return max(1, (viewport_width - 28) // (GameCard.CARD_WIDTH + 16))

    def _get_filtered_games(self) -> list[Game]:
        if self._search_query:
            games = self.store.search_games(self._search_query)
        else:
            games = self.store.get_games_by_category(self._current_category)
        return self._sort_games(games)

    def _sort_games(self, games: list[Game]) -> list[Game]:
        key_fn = {
            "name": lambda g: g.name.lower(),
            "play_time": lambda g: -g.total_play_time,
            "last_played": lambda g: g.last_played or "0",
            "added_time": lambda g: g.added_time,
        }.get(self._sort_mode)
        if key_fn:
            if self._sort_mode == "last_played":
                games.sort(key=key_fn, reverse=True)
            else:
                games.sort(key=key_fn)
        return games

    def _on_sort_changed(self, index: int):
        modes = ["name", "play_time", "last_played", "added_time"]
        self._sort_mode = modes[index]
        self.store.sort_mode = self._sort_mode
        self.store.save_config()
        self._refresh_cards(force=True)

    # --- 事件处理 ---

    def _on_category_changed(self, category: str):
        self._current_category = category
        self._search_query = ""
        self.sidebar.search_box.clear()
        self._refresh_cards(force=True)

    def _on_search_changed(self, query: str):
        self._search_query = query
        self._refresh_cards(force=True)

    def _show_detail(self, game_id: str):
        game = self.store.get_game(game_id)
        if game:
            self._selected_game_id = game_id
            self.detail_page.set_game(game, self.launcher.is_running(game_id))
            self.scroll_area.hide()
            self.detail_page.show()

    def _close_detail(self):
        self.detail_page.hide()
        self.scroll_area.show()
        self._selected_game_id = None

    def _toggle_game(self, game_id: str):
        game = self.store.get_game(game_id)
        if not game:
            return

        if self.launcher.is_running(game_id):
            self.launcher.terminate(game_id)
        else:
            success = self.launcher.launch(game_id, game.exe_path, game.launch_args)
            if not success:
                QMessageBox.warning(self, "启动失败", f"无法启动游戏\n请检查路径是否正确:\n{game.exe_path}")

    def _on_game_started(self, game_id: str):
        self.tracker.start_session(game_id)
        game = self.store.get_game(game_id)
        if game:
            game.is_running = True
        self._update_card_state(game_id)
        self._refresh_sidebar_counts()
        if self._selected_game_id == game_id:
            self.detail_page.set_running(True)

    def _on_game_exited(self, game_id: str):
        self.tracker.end_session(game_id)
        game = self.store.get_game(game_id)
        if game:
            game.is_running = False
        self._update_card_state(game_id)
        self._refresh_sidebar_counts()
        if self._selected_game_id == game_id:
            self.detail_page.set_game(game, False)

    def _update_card_state(self, game_id: str):
        card = self._cards.get(game_id)
        if card:
            game = self.store.get_game(game_id)
            if game:
                card.update_game(game)

    def _refresh_sidebar_counts(self):
        """仅更新侧边栏计数，不重建按钮"""
        counts = {"全部": len(self.store.games)}
        recent = [g for g in self.store.games if g.last_played]
        counts["最近游玩"] = len(recent)
        for game in self.store.games:
            counts[game.category] = counts.get(game.category, 0) + 1
        self.sidebar.update_counts(counts)

    def _add_game(self):
        cat = self._current_category if self._current_category not in ("全部", "最近游玩") else "其他"
        dialog = AddGameDialog(self.store, default_category=cat, parent=self)
        if dialog.exec():
            self._refresh()

    def _edit_game(self, game_id: str):
        game = self.store.get_game(game_id)
        if game:
            dialog = AddGameDialog(self.store, game=game, parent=self)
            if dialog.exec():
                self._refresh()
                if self._selected_game_id == game_id:
                    self.detail_page.set_game(self.store.get_game(game_id), self.launcher.is_running(game_id))

    def _delete_game(self, game_id: str):
        game = self.store.get_game(game_id)
        if not game:
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除「{game.name}」吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        if self.launcher.is_running(game_id):
            self.launcher.terminate(game_id)
        self.store.remove_game(game_id)
        if self._selected_game_id == game_id:
            self._close_detail()
        self._refresh()

    def _scan_directory(self):
        start_dir = self.store.default_game_dir or ""
        path = QFileDialog.getExistingDirectory(self, "选择游戏目录进行扫描", start_dir)
        if not path:
            return

        found = self.scanner.scan_directory(path)
        if not found:
            QMessageBox.information(self, "扫描结果", "未找到游戏文件")
            return

        # 将扫描到的游戏归入当前分类
        cat = self._current_category if self._current_category not in ("全部", "最近游玩") else "其他"
        for game in found:
            game.category = cat

        # 按路径去重，标记已有游戏
        existing_paths = {os.path.normpath(g.exe_path).lower() for g in self.store.games}
        existing_names = {g.name.lower() for g in self.store.games}

        # 使用扫描结果对话框，让用户逐条确认（包含已有项标记）
        dialog = ScanResultDialog(found, self, existing_paths=existing_paths, existing_names=existing_names)
        if dialog.exec():
            for game in dialog.get_selected_games():
                game.category = cat
                self.store.add_game(game)
            self._refresh()

    def _manual_select(self):
        """手动选择可执行文件添加为游戏，支持跨目录多次选择"""
        try:
            cat = self._current_category if self._current_category not in ("全部", "最近游玩") else "其他"
            existing_paths = {os.path.normpath(g.exe_path).lower() for g in self.store.games}
            existing_names = {g.name.lower() for g in self.store.games}
            all_new_games = []
            seen_paths = set()

            while True:
                start_dir = self.store.default_game_dir or ""
                files, _ = QFileDialog.getOpenFileNames(
                    self, "选择游戏可执行文件", start_dir,
                    "可执行文件 (*.exe *.bat *.cmd);;所有文件 (*.*)"
                )
                if not files and not all_new_games:
                    return
                if not files:
                    break

                for path in files:
                    norm = os.path.normpath(path).lower()
                    if norm in seen_paths:
                        continue
                    seen_paths.add(norm)
                    name = get_exe_name(path)
                    game = Game(name=name, exe_path=path, category=cat)
                    all_new_games.append(game)

                if not all_new_games:
                    QMessageBox.information(self, "提示", "选择的文件已在列表中")
                    return

                dialog = ScanResultDialog(all_new_games, self, allow_add_more=True,
                                          existing_paths=existing_paths, existing_names=existing_names)
                result = dialog.exec()
                all_new_games = dialog.get_selected_games()
                if result == ScanResultDialog.ADD_MORE_RESULT:
                    continue
                elif result == 1:  # QDialog.Accepted
                    for game in all_new_games:
                        self.store.add_game(game)
                    self._refresh()
                    return
                else:
                    return
        except Exception:
            traceback.print_exc()
            QMessageBox.critical(self, "手动选择出错", traceback.format_exc()[:500])

    def _on_cover_changed(self, path: str):
        if self.detail_page.game:
            self.detail_page.game.cover_path = path
            self.store.update_game(self.detail_page.game)
            self._update_card_state(self.detail_page.game.id)

    def _on_desc_changed(self, text: str):
        if self.detail_page.game:
            self.detail_page.game.description = text
            self.store.update_game(self.detail_page.game)

    def _toggle_privacy(self, enabled: bool):
        """切换隐私模式，刷新所有卡片和详情页"""
        self.store.privacy_mode = enabled
        self.store.save_config()
        # 刷新卡片
        for card in self._cards.values():
            card.set_privacy_mode(enabled)
        # 刷新详情页
        if self.detail_page.game and self.detail_page.isVisible():
            self.detail_page.set_game(self.detail_page.game, self._selected_game_id and self.launcher.is_running(self._selected_game_id))

    def _on_search_engine_changed(self, engine: str):
        """更新默认搜索引擎"""
        self.store.default_search_engine = engine
        self.store.save_config()

    def _on_game_dir_changed(self, path: str):
        """更新默认游戏库目录"""
        self.store.default_game_dir = path
        self.store.save_config()

    def _on_theme_changed(self, theme_name: str):
        """切换主题"""
        from PyQt6.QtWidgets import QApplication
        from ui.styles import THEMES
        self.store.theme = theme_name
        self.store.save_config()
        QApplication.instance().setStyleSheet(THEMES.get(theme_name, THEMES["暗夜"]))

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _apply_frameless_mode(self, enabled: bool):
        """应用/取消无边框模式"""
        was_visible = self.isVisible()
        was_maximized = self.isMaximized()

        # 保存窗口外部几何（含框架），切换标志后恢复，防止标题栏跑出屏幕
        frame_geo = self.frameGeometry() if was_visible and not was_maximized else None
        if was_maximized:
            self.showNormal()

        if enabled:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
            self._main_layout.setContentsMargins(5, 5, 5, 5)
            self._set_resize_mouse_tracking(True)
            QApplication.instance().installEventFilter(self)
            self._btn_minimize.show()
            self._btn_maximize.show()
            self._btn_close.show()
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.FramelessWindowHint)
            self._main_layout.setContentsMargins(0, 0, 0, 0)
            self._set_resize_mouse_tracking(False)
            QApplication.instance().removeEventFilter(self)
            self._restore_override_cursor()
            self._btn_minimize.hide()
            self._btn_maximize.hide()
            self._btn_close.hide()
        self.store.frameless_mode = enabled
        self.store.save_config()

        if was_maximized:
            self.showMaximized()
        elif was_visible and frame_geo is not None:
            self.setGeometry(frame_geo)
            self.show()
            # show() 后原生窗口可能被系统重新定位，下一轮事件循环强制校准
            QTimer.singleShot(0, lambda: self._clamp_to_screen())

    def _clamp_to_screen(self):
        """确保窗口框架顶部不低于屏幕可用区域顶部"""
        screen = QApplication.instance().primaryScreen()
        if screen is None:
            return
        top = screen.availableGeometry().top()
        fg = self.frameGeometry()
        if fg.top() < top:
            self.move(fg.left(), top)

    # ---- 无边框边缘拖拽缩放 ----

    _EDGE_MARGIN = 5  # 边缘检测范围（px），与 _main_layout margins 保持一致

    def _set_resize_mouse_tracking(self, enabled):
        """递归启用/禁用 central widget 及其所有子孙的 mouseTracking"""
        central = self.centralWidget()
        central.setMouseTracking(enabled)
        for w in central.findChildren(QFrame):
            w.setMouseTracking(enabled)

    def _hit_edge(self, pos):
        """返回鼠标位置对应的窗口边缘 Qt.Edge，不在边缘返回 None"""
        m = self._EDGE_MARGIN
        r = self.rect()
        l = pos.x() < m
        ri = pos.x() > r.width() - m
        t = pos.y() < m
        b = pos.y() > r.height() - m
        if t and l:    return Qt.Edge.TopEdge | Qt.Edge.LeftEdge
        if t and ri:   return Qt.Edge.TopEdge | Qt.Edge.RightEdge
        if b and l:    return Qt.Edge.BottomEdge | Qt.Edge.LeftEdge
        if b and ri:   return Qt.Edge.BottomEdge | Qt.Edge.RightEdge
        if t:          return Qt.Edge.TopEdge
        if b:          return Qt.Edge.BottomEdge
        if l:          return Qt.Edge.LeftEdge
        if ri:         return Qt.Edge.RightEdge
        return None

    @staticmethod
    def _edge_cursor(edge):
        """映射 Qt.Edge → CursorShape"""
        if edge == Qt.Edge.TopEdge or edge == Qt.Edge.BottomEdge:
            return Qt.CursorShape.SizeVerCursor
        if edge == Qt.Edge.LeftEdge or edge == Qt.Edge.RightEdge:
            return Qt.CursorShape.SizeHorCursor
        if edge == (Qt.Edge.TopEdge | Qt.Edge.LeftEdge) or edge == (Qt.Edge.BottomEdge | Qt.Edge.RightEdge):
            return Qt.CursorShape.SizeFDiagCursor
        return Qt.CursorShape.SizeBDiagCursor

    def _set_override_cursor(self, shape):
        if not self._override_cursor_active:
            QApplication.setOverrideCursor(shape)
            self._override_cursor_active = True

    def _restore_override_cursor(self):
        if self._override_cursor_active:
            QApplication.restoreOverrideCursor()
            self._override_cursor_active = False

    def eventFilter(self, obj, event):
        if not self.store.frameless_mode or self.isMaximized():
            return super().eventFilter(obj, event)

        # 只处理 MainWindow 自身 widget 的事件，对话框/弹出窗口放行
        if isinstance(obj, QWidget) and obj.window() is not self:
            return super().eventFilter(obj, event)
        # 有模态对话框激活时也放行，防止对话框控件触发边缘缩放
        if QApplication.activeModalWidget() is not None:
            return super().eventFilter(obj, event)

        t = event.type()

        if t == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                pos = self.mapFromGlobal(event.globalPosition().toPoint())
                edge = self._hit_edge(pos)
                if edge is not None:
                    self._resize_edge = edge
                    self._resize_start_geo = self.geometry()
                    self._resize_start_pos = event.globalPosition().toPoint()
                    return True

        elif t == QEvent.Type.MouseMove:
            if self._resize_edge is not None:
                self._do_resize(event.globalPosition().toPoint())
                return True
            pos = self.mapFromGlobal(event.globalPosition().toPoint())
            edge = self._hit_edge(pos)
            if edge is not None:
                self._set_override_cursor(self._edge_cursor(edge))
            else:
                self._restore_override_cursor()

        elif t == QEvent.Type.MouseButtonRelease:
            if self._resize_edge is not None:
                self._resize_edge = None
                self._resize_start_geo = None
                self._resize_start_pos = None
                self._restore_override_cursor()
                return True

        elif t == QEvent.Type.Leave:
            if obj is self.centralWidget() and self._resize_edge is None:
                self._restore_override_cursor()

        return super().eventFilter(obj, event)

    def _do_resize(self, global_pos):
        delta = global_pos - self._resize_start_pos
        geo = self._resize_start_geo
        edge = self._resize_edge
        min_w, min_h = self.minimumWidth(), self.minimumHeight()

        top, left, right, bottom = geo.top(), geo.left(), geo.right(), geo.bottom()

        if edge & Qt.Edge.TopEdge:
            new_top = top + delta.y()
            if bottom - new_top >= min_h:
                top = new_top
        if edge & Qt.Edge.BottomEdge:
            new_bottom = bottom + delta.y()
            if new_bottom - top >= min_h:
                bottom = new_bottom
        if edge & Qt.Edge.LeftEdge:
            new_left = left + delta.x()
            if right - new_left >= min_w:
                left = new_left
        if edge & Qt.Edge.RightEdge:
            new_right = right + delta.x()
            if new_right - left >= min_w:
                right = new_right

        self.setGeometry(left, top, right - left, bottom - top)

    def _on_frameless_mode_changed(self, enabled: bool):
        """设置窗口 frameless 模式切换"""
        self._apply_frameless_mode(enabled)

    def changeEvent(self, event):
        if event.type() == event.Type.WindowStateChange:
            self._btn_maximize.set_maximized_state(self.isMaximized())
            if self.store.frameless_mode:
                if self.isMaximized():
                    self._main_layout.setContentsMargins(0, 0, 0, 0)
                    self._restore_override_cursor()
                else:
                    self._main_layout.setContentsMargins(5, 5, 5, 5)
        super().changeEvent(event)

    def _show_settings(self):
        dialog = SettingsDialog(
            self.store.data_dir, self.store.privacy_mode,
            self.store.categories, self.store.default_search_engine,
            self.store.default_game_dir, self.store.theme,
            self.store.frameless_mode, self
        )
        # 确保 dialog 有独立窗口装饰，不受 frameless 父窗口影响
        flags = Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowTitleHint
        if self.store.frameless_mode:
            dialog.setWindowFlags(flags)
            dialog.move(self.geometry().center() - dialog.rect().center())
        dialog.privacy_mode_changed.connect(self._toggle_privacy)
        dialog.search_engine_changed.connect(self._on_search_engine_changed)
        dialog.game_dir_changed.connect(self._on_game_dir_changed)
        dialog.theme_changed.connect(self._on_theme_changed)
        dialog.frameless_mode_changed.connect(self._on_frameless_mode_changed)
        # 实时刷新侧边栏（不保存，仅预览）
        dialog.categories_changed.connect(self._refresh)
        dialog.exec()
        # 对话框关闭后统一同步分类到 store
        self._sync_categories(dialog._categories)

    def _sync_categories(self, new_cats: list[str]):
        """同步分类列表到 store，处理被删除分类的游戏"""
        removed = [c for c in self.store.categories if c not in new_cats]
        self.store.categories = list(new_cats)
        for cat in removed:
            for g in self.store.games:
                if g.category == cat:
                    g.category = "其他"
        self.store.save()
        self._refresh()

    def showEvent(self, event):
        super().showEvent(event)
        if self._splash_overlay:
            QTimer.singleShot(400, self._start_splash_anim)

    def _setup_splash_overlay(self):
        """创建开屏覆盖层，等 showEvent 后再启动渐变动画"""
        colors = self._splash_colors()

        overlay = QWidget(self)
        overlay.setGeometry(0, 0, self.width(), self.height())
        overlay.setStyleSheet(f"background-color: {colors['bg_primary']};")
        overlay.raise_()

        layout = QVBoxLayout(overlay)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel("▶")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(f"color: {colors['accent']}; font-size: 56px; background: transparent;")
        layout.addWidget(icon)

        title = QLabel("GameHub")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("Microsoft YaHei", 30)
        font.setBold(True)
        title.setFont(font)
        title.setStyleSheet(f"color: {colors['text_primary']}; font-size: 30px; font-weight: bold; background: transparent;")
        layout.addWidget(title)

        layout.addSpacing(4)

        subtitle = QLabel("本地游戏管理器")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"color: {colors['text_muted']}; font-size: 14px; background: transparent;")
        layout.addWidget(subtitle)

        # 用 QGraphicsOpacityEffect 统一控制透明度
        self._splash_effect = QGraphicsOpacityEffect(overlay)
        self._splash_effect.setOpacity(1.0)
        overlay.setGraphicsEffect(self._splash_effect)

        overlay.show()
        self._splash_overlay = overlay

    def _start_splash_anim(self):
        self._splash_anim = QPropertyAnimation(self._splash_effect, b"opacity")
        self._splash_anim.setDuration(700)
        self._splash_anim.setStartValue(1.0)
        self._splash_anim.setEndValue(0.0)
        self._splash_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._splash_anim.finished.connect(self._on_splash_finished)
        self._splash_anim.start()

    def _on_splash_finished(self):
        self._splash_overlay.hide()
        self._splash_overlay.deleteLater()
        self._splash_overlay = None
        self._splash_effect = None
        self._splash_anim = None

    def _splash_colors(self) -> dict:
        from ui.styles import _COLORS
        theme = getattr(self.store, 'theme', '暗夜')
        return _COLORS.get(theme, _COLORS['暗夜'])

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_timer.start()  # 防抖：停止拖动后才刷新

    def closeEvent(self, event):
        self.launcher.shutdown_all()
        # 结束所有追踪中的会话
        for game_id in list(self.tracker._active_sessions.keys()):
            self.tracker.end_session(game_id)
        super().closeEvent(event)
