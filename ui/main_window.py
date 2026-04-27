"""主窗口 - 整合侧边栏、游戏卡片网格、详情面板"""
import os

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QScrollArea, QGridLayout,
    QFrame, QFileDialog, QMessageBox, QComboBox, QDialog,
    QGraphicsOpacityEffect, QApplication, QMenu
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QShortcut, QKeySequence, QFont

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
from ui.widgets.win_control_button import WinControlButton
from ui.widgets.frameless_toolbar import FramelessToolbar
from ui.widgets.frameless_resize_mixin import FramelessResizeMixin
from ui.styles import THEMES, _COLORS
from utils.file_utils import get_exe_name

_SORT_LABELS = ["名称", "游玩时长", "最近游玩", "添加时间"]
_SORT_MODES = ["name", "play_time", "last_played", "added_time"]


class MainWindow(FramelessResizeMixin, QMainWindow):
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

        self.init_resize_state()

        # 防抖：resize 时延迟刷新卡片，避免拖动卡顿
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(50)
        self._resize_timer.timeout.connect(self._refresh_cards)

        self._setup_ui()
        self._connect_signals()
        self._setup_shortcuts()
        self._splash_started = False
        self._setup_splash_overlay()
        # 若以无边框模式启动，先用正常窗口短暂 show 一次，
        # 让 Windows DWM 记录窗口的带边框状态，之后切换才能正确渲染边框
        if self.store.frameless_mode:
            self.setWindowOpacity(0.0)
            self.show()
            self.hide()
            self.setWindowOpacity(1.0)
        self._apply_frameless_mode(self.store.frameless_mode)
        self._refresh()

    @property
    def _default_category(self) -> str:
        return self._current_category if self._current_category not in ("全部", "最近游玩") else "其他"

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

        # 库概览
        self.overview_panel = self._create_overview_panel()
        self.grid_layout.addWidget(self.overview_panel)

        # 卡片网格
        self.card_grid = QGridLayout()
        self.card_grid.setSpacing(16)
        self.grid_layout.addLayout(self.card_grid)

        # 空状态提示
        self.empty_state = self._create_empty_state()
        self.grid_layout.addWidget(self.empty_state)
        self.empty_state.hide()

        self.scroll_area.setWidget(self.grid_container)
        content_layout.addWidget(self.scroll_area, 1)

        main_layout.addWidget(content, 1)

        # 详情页面（默认隐藏，替换卡片网格显示）
        self.detail_page = GameDetailPage()
        self.detail_page.hide()
        content_layout.addWidget(self.detail_page, 1)

    def _create_overview_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("library-overview")
        panel.setMinimumHeight(116)
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(18)

        copy = QVBoxLayout()
        copy.setSpacing(4)
        kicker = QLabel("LIBRARY")
        kicker.setObjectName("overview-kicker")
        self.overview_title = QLabel("全部游戏")
        self.overview_title.setObjectName("overview-title")
        self.overview_subtitle = QLabel("整理、启动和回顾你的本地游戏库")
        self.overview_subtitle.setObjectName("overview-subtitle")
        copy.addWidget(kicker)
        copy.addWidget(self.overview_title)
        copy.addWidget(self.overview_subtitle)
        layout.addLayout(copy, 1)

        self._overview_stats = {}
        for key, label in (
            ("shown", "当前"),
            ("played", "已游玩"),
            ("recent", "有记录"),
            ("hours", "总时长"),
        ):
            stat = QWidget()
            stat.setObjectName("overview-stat")
            stat_layout = QVBoxLayout(stat)
            stat_layout.setContentsMargins(14, 10, 14, 10)
            stat_layout.setSpacing(2)
            value = QLabel("0")
            value.setObjectName("overview-stat-value")
            caption = QLabel(label)
            caption.setObjectName("overview-stat-label")
            stat_layout.addWidget(value)
            stat_layout.addWidget(caption)
            layout.addWidget(stat)
            self._overview_stats[key] = value

        return panel

    def _create_empty_state(self) -> QWidget:
        empty = QWidget()
        empty.setObjectName("empty-state")
        layout = QVBoxLayout(empty)
        layout.setContentsMargins(24, 46, 24, 46)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        mark = QLabel("◇")
        mark.setObjectName("empty-mark")
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(mark)

        title = QLabel("还没有游戏")
        title.setObjectName("empty-title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("添加一个可执行文件，或者扫描你的游戏目录。")
        subtitle.setObjectName("empty-subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        action_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        add_btn = QPushButton("+ 添加游戏")
        add_btn.setObjectName("empty-primary-btn")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add_game)
        action_row.addWidget(add_btn)

        scan_btn = QPushButton("扫描目录")
        scan_btn.setObjectName("empty-secondary-btn")
        scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        scan_btn.clicked.connect(self._scan_directory)
        action_row.addWidget(scan_btn)

        layout.addLayout(action_row)
        return empty

    def _create_toolbar(self) -> QWidget:
        toolbar = FramelessToolbar(lambda: self.store.frameless_mode)
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
        self.sort_combo.addItems(_SORT_LABELS)
        self.sort_combo.setCurrentIndex(_SORT_MODES.index(self._sort_mode) if self._sort_mode in _SORT_MODES else 0)
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        layout.addWidget(self.sort_combo)

        layout.addSpacing(12)

        # 添加游戏菜单
        add_btn = QPushButton("+ 添加游戏")
        add_btn.setObjectName("add-game-btn")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setToolTip("添加单个游戏、批量选择或扫描目录")
        add_menu = QMenu(add_btn)
        add_menu.setObjectName("add-game-menu")
        add_single_action = add_menu.addAction("添加单个游戏")
        add_single_action.triggered.connect(self._add_game)
        add_multi_action = add_menu.addAction("手动多选")
        add_multi_action.triggered.connect(self._manual_select)
        add_menu.addSeparator()
        scan_action = add_menu.addAction("扫描目录")
        scan_action.triggered.connect(self._scan_directory)
        add_btn.clicked.connect(lambda: add_menu.exec(add_btn.mapToGlobal(add_btn.rect().bottomLeft())))
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
        self._btn_minimize = WinControlButton('min')
        self._btn_minimize.setObjectName("win-control-btn")
        self._btn_minimize.clicked.connect(self.showMinimized)
        self._btn_minimize.hide()
        layout.addWidget(self._btn_minimize)

        self._btn_maximize = WinControlButton('max')
        self._btn_maximize.setObjectName("win-control-btn")
        self._btn_maximize.clicked.connect(self._toggle_maximize)
        self._btn_maximize.hide()
        layout.addWidget(self._btn_maximize)

        self._btn_close = WinControlButton('close')
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

    def _compute_category_counts(self) -> dict:
        counts = {"全部": len(self.store.games)}
        recent = [g for g in self.store.games if g.last_played]
        counts["最近游玩"] = len(recent)
        for game in self.store.games:
            counts[game.category] = counts.get(game.category, 0) + 1
        return counts

    def _refresh(self):
        """刷新界面"""
        counts = self._compute_category_counts()

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
        self._update_overview(games)

        # 空状态
        if not games:
            self.empty_state.show()
            return

        self.empty_state.hide()

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
            reverse = self._sort_mode == "last_played"
            games.sort(key=key_fn, reverse=reverse)
        return games

    def _update_overview(self, shown_games: list[Game]):
        played = sum(1 for g in shown_games if g.total_play_time > 0)
        recent = sum(1 for g in shown_games if g.last_played)
        total_hours = int(sum(g.total_play_time for g in shown_games) // 3600)
        self._overview_stats["shown"].setText(str(len(shown_games)))
        self._overview_stats["played"].setText(str(played))
        self._overview_stats["recent"].setText(str(recent))
        self._overview_stats["hours"].setText(f"{total_hours}h")

        if self._search_query:
            self.overview_title.setText(f"搜索「{self._search_query}」")
            self.overview_subtitle.setText("从当前游戏库中筛选匹配项")
        elif self._current_category == "全部":
            self.overview_title.setText("全部游戏")
            self.overview_subtitle.setText("整理、启动和回顾你的本地游戏库")
        elif self._current_category == "最近游玩":
            self.overview_title.setText("最近游玩")
            self.overview_subtitle.setText("快速回到近期打开过的游戏")
        else:
            self.overview_title.setText(self._current_category)
            self.overview_subtitle.setText("当前分类下的游戏集合")

    def _on_sort_changed(self, index: int):
        self._sort_mode = _SORT_MODES[index]
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
        self.sidebar.update_counts(self._compute_category_counts())

    def _add_game(self):
        cat = self._default_category
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
        cat = self._default_category
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
        cat = self._default_category
        existing_paths = {os.path.normpath(g.exe_path).lower() for g in self.store.games}
        existing_names = {g.name.lower() for g in self.store.games}
        pending: list[Game] = []
        seen = set()

        while True:
            start_dir = self.store.default_game_dir or ""
            files, _ = QFileDialog.getOpenFileNames(
                self, "选择游戏可执行文件", start_dir,
                "可执行文件 (*.exe *.bat *.cmd);;所有文件 (*.*)"
            )
            if not files:
                if not pending:
                    return
                break

            for path in files:
                norm = os.path.normpath(path).lower()
                if norm in seen:
                    continue
                seen.add(norm)
                pending.append(Game(name=get_exe_name(path), exe_path=path, category=cat))

            dlg = ScanResultDialog(pending, self, allow_add_more=True,
                                   existing_paths=existing_paths, existing_names=existing_names)
            action = dlg.exec()
            pending = dlg.get_selected_games()

            if action == ScanResultDialog.ADD_MORE_RESULT:
                continue
            if action == QDialog.DialogCode.Accepted:
                for g in pending:
                    self.store.add_game(g)
                self._refresh()
            return

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
            running = self._selected_game_id and self.launcher.is_running(self._selected_game_id)
            self.detail_page.set_game(self.detail_page.game, running)

    def _on_search_engine_changed(self, engine: str):
        """更新默认搜索引擎"""
        self.store.default_search_engine = engine
        self.store.save_config()

    def _on_game_dir_changed(self, path: str):
        """更新默认游戏库目录"""
        self.store.default_game_dir = path
        self.store.save_config()

    def _on_theme_changed(self, theme_name: str):
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

        # 先隐藏，然后改标志，再显示，确保原生窗口框架正确重建
        self.hide()

        if enabled:
            self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
            self._main_layout.setContentsMargins(5, 5, 5, 5)
            self._set_resize_mouse_tracking(True)
            QApplication.instance().installEventFilter(self)
            self._btn_minimize.show()
            self._btn_maximize.show()
            self._btn_close.show()
        else:
            self.setWindowFlag(Qt.WindowType.FramelessWindowHint, False)
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
            self.show()
            self.setGeometry(frame_geo)
            # show() 后原生窗口可能被系统重新定位，下一轮事件循环强制校准
            QTimer.singleShot(0, lambda: self._clamp_to_screen())
        elif not was_visible:
            pass  # 保持隐藏

    def _clamp_to_screen(self):
        """确保窗口框架顶部不低于屏幕可用区域顶部"""
        screen = QApplication.instance().primaryScreen()
        if screen is None:
            return
        top = screen.availableGeometry().top()
        fg = self.frameGeometry()
        if fg.top() < top:
            self.move(fg.left(), top)

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
        dialog = SettingsDialog(self.store, self)
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
        if self._splash_overlay and not self._splash_started:
            self._splash_started = True
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
