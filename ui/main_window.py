"""主窗口 - 整合侧边栏、游戏卡片网格、详情面板"""
import os
import traceback

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QScrollArea, QGridLayout,
    QFrame, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer

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
        self._selected_game_id = None
        self._cards: dict[str, "GameCard"] = {}  # game_id -> GameCard 快速查找

        # 防抖：resize 时延迟刷新卡片，避免拖动卡顿
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(150)
        self._resize_timer.timeout.connect(self._refresh_cards)

        self._setup_ui()
        self._connect_signals()
        self._refresh()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

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
        self.grid_layout.setContentsMargins(20, 16, 20, 16)
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

    def _create_toolbar(self) -> QWidget:
        toolbar = QWidget()
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

    def _refresh(self):
        """刷新界面"""
        # 更新侧边栏
        counts = {"全部": len(self.store.games)}
        recent = [g for g in self.store.games if g.last_played]
        counts["最近游玩"] = len(recent)
        for game in self.store.games:
            counts[game.category] = counts.get(game.category, 0) + 1

        self.sidebar.set_categories(self.store.categories, counts)
        self.sidebar.update_counts(counts)

        # 刷新卡片
        self._refresh_cards()

    def _refresh_cards(self):
        """刷新游戏卡片"""
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

        # 计算列数（首次加载时 viewport 可能尚未布局，用窗口宽度估算）
        viewport_width = self.scroll_area.viewport().width()
        if viewport_width <= 100:
            viewport_width = max(800, self.width() - 260)
        cols = max(1, (viewport_width - 40) // (GameCard.CARD_WIDTH + 16))

        for i, game in enumerate(games):
            card = GameCard(game)
            card.set_privacy_mode(self.store.privacy_mode)
            card.play_clicked.connect(self._toggle_game)
            card.detail_clicked.connect(self._show_detail)
            card.delete_clicked.connect(self._delete_game)
            row, col = divmod(i, cols)
            self.card_grid.addWidget(card, row, col)
            self._cards[game.id] = card

    def _get_filtered_games(self) -> list[Game]:
        if self._search_query:
            return self.store.search_games(self._search_query)
        return self.store.get_games_by_category(self._current_category)

    # --- 事件处理 ---

    def _on_category_changed(self, category: str):
        self._current_category = category
        self._search_query = ""
        self.sidebar.search_box.clear()
        self._refresh_cards()

    def _on_search_changed(self, query: str):
        self._search_query = query
        self._refresh_cards()

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
        if self._selected_game_id == game_id:
            self.detail_page.set_running(True)

    def _on_game_exited(self, game_id: str):
        self.tracker.end_session(game_id)
        game = self.store.get_game(game_id)
        if game:
            game.is_running = False
        self._update_card_state(game_id)
        if self._selected_game_id == game_id:
            self.detail_page.set_game(game, False)

    def _update_card_state(self, game_id: str):
        card = self._cards.get(game_id)
        if card:
            game = self.store.get_game(game_id)
            if game:
                card.update_game(game)

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

    def _show_settings(self):
        dialog = SettingsDialog(
            self.store.data_dir, self.store.privacy_mode,
            self.store.categories, self.store.default_search_engine,
            self.store.default_game_dir, self
        )
        dialog.privacy_mode_changed.connect(self._toggle_privacy)
        dialog.search_engine_changed.connect(self._on_search_engine_changed)
        dialog.game_dir_changed.connect(self._on_game_dir_changed)
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
        # 首次显示时 viewport 宽度才确定，需要重新刷新卡片布局
        QTimer.singleShot(50, self._refresh_cards)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_timer.start()  # 防抖：停止拖动后才刷新

    def closeEvent(self, event):
        self.launcher.shutdown_all()
        # 结束所有追踪中的会话
        for game_id in list(self.tracker._active_sessions.keys()):
            self.tracker.end_session(game_id)
        super().closeEvent(event)
