"""设置对话框"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QFormLayout, QLineEdit, QCheckBox,
    QWidget, QScrollArea, QFrame, QComboBox, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal

from ui.widgets.frameless_dialog import FramelessDialogTitleBar, apply_dialog_frameless

# 不可删除的分类
FIXED_CATEGORIES = {"全部", "最近游玩"}


class SettingsDialog(QDialog):
    """应用设置"""

    privacy_mode_changed = pyqtSignal(bool)  # 隐私模式变更信号
    categories_changed = pyqtSignal(list)    # 分类变更信号
    game_dir_changed = pyqtSignal(str)       # 默认游戏库目录变更信号
    theme_changed = pyqtSignal(str)          # 主题变更信号
    startup_page_changed = pyqtSignal(str)   # 启动页变更信号
    library_entry_category_changed = pyqtSignal(str)  # 进入游戏库默认分类变更信号
    frameless_mode_changed = pyqtSignal(bool)  # 无边框模式变更信号

    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.data_dir = store.data_dir
        self._privacy_mode = store.privacy_mode
        self._categories = list(store.categories)
        self._default_game_dir = store.default_game_dir
        self._default_theme = store.theme
        self._startup_page = store.startup_page
        self._library_entry_category = getattr(store, "library_entry_category", "last")
        self._frameless_mode = store.frameless_mode
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("设置")
        self.setMinimumSize(600, 520)
        self.resize(680, 620)
        self.setModal(True)
        self.setSizeGripEnabled(True)
        if self._frameless_mode:
            apply_dialog_frameless(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(16)

        if self._frameless_mode:
            layout.addWidget(FramelessDialogTitleBar("设置", self))
        else:
            title = QLabel("设置")
            title.setObjectName("dialog-title")
            layout.addWidget(title)

        # 标签页
        tabs = QTabWidget()
        tabs.addTab(self._scrollable_tab(self._create_general_tab()), "常规")
        tabs.addTab(self._scrollable_tab(self._create_appearance_tab()), "外观")
        tabs.addTab(self._scrollable_tab(self._create_categories_tab()), "分类")
        tabs.addTab(self._scrollable_tab(self._create_about_tab()), "关于")
        layout.addWidget(tabs)

        # 底部按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.setObjectName("primary-btn")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def _scrollable_tab(self, page: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setObjectName("settings-tab-scroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(page)
        return scroll

    def _create_general_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # 数据目录
        section = QLabel("数据管理")
        section.setObjectName("settings-section-title")
        layout.addWidget(section)

        form = QFormLayout()
        form.setSpacing(10)

        self.dir_input = QLineEdit(self.data_dir)
        self.dir_input.setReadOnly(True)
        form.addRow("数据目录:", self.dir_input)

        info = QLabel("数据目录存储游戏列表、封面和统计数据。\n更改目录不会移动现有数据。")
        info.setObjectName("detail-info")
        form.addRow("", info)

        layout.addLayout(form)
        layout.addSpacing(8)

        # 默认游戏库
        section2 = QLabel("游戏库")
        section2.setObjectName("settings-section-title")
        layout.addWidget(section2)

        form2 = QFormLayout()
        form2.setSpacing(10)

        game_dir_row = QHBoxLayout()
        self.game_dir_input = QLineEdit(self._default_game_dir)
        self.game_dir_input.setPlaceholderText("未设置")
        self.game_dir_input.editingFinished.connect(self._sync_game_dir_input)
        game_dir_btn = QPushButton("浏览")
        game_dir_btn.setObjectName("file-btn")
        game_dir_btn.clicked.connect(self._change_game_dir)
        game_dir_row.addWidget(self.game_dir_input, 1)
        game_dir_row.addWidget(game_dir_btn)
        form2.addRow("默认游戏库:", game_dir_row)

        game_dir_info = QLabel("选择文件或扫描目录时的默认起始路径")
        game_dir_info.setObjectName("detail-info")
        form2.addRow("", game_dir_info)

        layout.addLayout(form2)
        layout.addSpacing(8)

        # 启动页
        section_startup = QLabel("启动")
        section_startup.setObjectName("settings-section-title")
        layout.addWidget(section_startup)

        form_startup = QFormLayout()
        form_startup.setSpacing(10)

        self.startup_page_combo = QComboBox()
        self.startup_page_combo.addItem("启动首页", "start_home")
        self.startup_page_combo.addItem("全部游戏", "all")
        self.startup_page_combo.addItem("上次浏览位置", "last")
        idx = self.startup_page_combo.findData(self._startup_page)
        if idx >= 0:
            self.startup_page_combo.setCurrentIndex(idx)
        self.startup_page_combo.currentIndexChanged.connect(self._on_startup_page_changed)
        form_startup.addRow("默认启动页面:", self.startup_page_combo)

        startup_info = QLabel("启动首页提供最近继续和快速操作，适合作为打开应用时的默认页面。")
        startup_info.setObjectName("detail-info")
        form_startup.addRow("", startup_info)

        self.library_entry_combo = QComboBox()
        self._refresh_library_entry_combo()
        self.library_entry_combo.currentIndexChanged.connect(self._on_library_entry_category_changed)
        form_startup.addRow("进入游戏库默认分类:", self.library_entry_combo)

        library_entry_info = QLabel("从启动页进入游戏库时默认打开的分类；选择“上次浏览位置”可沿用最近一次浏览的分类。")
        library_entry_info.setObjectName("detail-info")
        form_startup.addRow("", library_entry_info)

        layout.addLayout(form_startup)
        layout.addSpacing(8)

        layout.addStretch()
        return page

    def _create_appearance_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # 主题
        section = QLabel("主题风格")
        section.setObjectName("settings-section-title")
        layout.addWidget(section)

        form = QFormLayout()
        form.setSpacing(10)

        self.theme_combo = QComboBox()
        self.theme_combo.addItem("暗夜")
        self.theme_combo.addItem("赛博朋克")
        self.theme_combo.addItem("毛玻璃")
        self.theme_combo.addItem("拟物质感")
        self.theme_combo.addItem("极简白")
        idx = self.theme_combo.findText(self._default_theme)
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        form.addRow("主题风格:", self.theme_combo)

        layout.addLayout(form)
        layout.addSpacing(8)

        # 隐私
        section2 = QLabel("隐私")
        section2.setObjectName("settings-section-title")
        layout.addWidget(section2)

        self.privacy_checkbox = QCheckBox("启用隐私模式")
        self.privacy_checkbox.setChecked(self._privacy_mode)
        self.privacy_checkbox.toggled.connect(self._on_privacy_toggled)
        layout.addWidget(self.privacy_checkbox)

        privacy_info = QLabel("开启后，已标记内容的封面将被打马赛克，名称将被遮蔽")
        privacy_info.setObjectName("detail-info")
        layout.addWidget(privacy_info)

        layout.addSpacing(8)

        # 窗口
        section3 = QLabel("窗口")
        section3.setObjectName("settings-section-title")
        layout.addWidget(section3)

        self.frameless_checkbox = QCheckBox("启用无边框模式")
        self.frameless_checkbox.setChecked(self._frameless_mode)
        self.frameless_checkbox.toggled.connect(self._on_frameless_toggled)
        layout.addWidget(self.frameless_checkbox)

        frameless_info = QLabel("开启后，窗口标题栏将集成到应用内部，工具栏可拖拽移动窗口")
        frameless_info.setObjectName("detail-info")
        layout.addWidget(frameless_info)

        layout.addStretch()
        return page

    def _create_categories_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        section = QLabel("分类管理")
        section.setObjectName("settings-section-title")
        layout.addWidget(section)

        info = QLabel("添加或删除游戏分类。删除分类后，该分类下的游戏将归入「其他」。")
        info.setObjectName("detail-info")
        info.setWordWrap(True)
        layout.addWidget(info)

        # 分类列表
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self._cat_list_widget = QWidget()
        self._cat_list_widget.setStyleSheet("background: transparent;")
        self._cat_list_layout = QVBoxLayout(self._cat_list_widget)
        self._cat_list_layout.setContentsMargins(0, 0, 0, 0)
        self._cat_list_layout.setSpacing(2)
        self._cat_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self._cat_list_widget)
        layout.addWidget(scroll, 1)

        # 添加分类行
        add_row = QHBoxLayout()
        add_row.setSpacing(8)
        self._new_cat_input = QLineEdit()
        self._new_cat_input.setPlaceholderText("输入新分类名称")
        self._new_cat_input.returnPressed.connect(self._add_category)
        add_row.addWidget(self._new_cat_input, 1)

        add_btn = QPushButton("添加")
        add_btn.setObjectName("primary-btn")
        add_btn.setMinimumWidth(70)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add_category)
        add_row.addWidget(add_btn)

        layout.addLayout(add_row)

        self._refresh_cat_list()
        return page

    def _create_about_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        section = QLabel("关于 GameHub")
        section.setObjectName("settings-section-title")
        layout.addWidget(section)

        about_lines = [
            ("版本:", "v1.0.0"),
            ("技术栈:", "Python 3.10+ / PyQt6"),
            ("简介:", "GameHub 是一款本地游戏管理器，支持游戏扫描导入、\n分类管理、封面展示、游玩记录追踪等功能。"),
        ]

        form = QFormLayout()
        form.setSpacing(10)
        for label, value in about_lines:
            lbl = QLabel(label)
            lbl.setObjectName("detail-info")
            val = QLabel(value)
            val.setObjectName("settings-cat-label")
            val.setWordWrap(True)
            val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            form.addRow(lbl, val)

        layout.addLayout(form)
        layout.addStretch()
        return page

    def _refresh_library_entry_combo(self):
        if not hasattr(self, "library_entry_combo"):
            return
        current = self._library_entry_category
        self.library_entry_combo.blockSignals(True)
        self.library_entry_combo.clear()
        self.library_entry_combo.addItem("上次浏览位置", "last")
        for cat in self._categories:
            self.library_entry_combo.addItem(cat, cat)
        idx = self.library_entry_combo.findData(current)
        if idx < 0:
            idx = self.library_entry_combo.findData("last")
            self._library_entry_category = "last"
        self.library_entry_combo.setCurrentIndex(max(0, idx))
        self.library_entry_combo.blockSignals(False)

    def _refresh_cat_list(self):
        """刷新分类列表"""
        # 清除旧项
        while self._cat_list_layout.count():
            item = self._cat_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for cat in self._categories:
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(4, 3, 4, 3)
            row_layout.setSpacing(8)

            cat_label = QLabel(cat)
            cat_label.setObjectName("settings-cat-label")
            cat_label.setStyleSheet("font-size: 13px; background: transparent;")

            is_fixed = cat in FIXED_CATEGORIES
            if is_fixed:
                cat_label.setObjectName("detail-info")

            row_layout.addWidget(cat_label, 1)

            if not is_fixed:
                del_btn = QPushButton("删除")
                del_btn.setFixedSize(52, 26)
                del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                del_btn.setObjectName("small-delete-btn")
                del_btn.clicked.connect(lambda checked, c=cat: self._remove_category(c))
                row_layout.addWidget(del_btn)

            self._cat_list_layout.addWidget(row)

    def _add_category(self):
        name = self._new_cat_input.text().strip()
        if not name:
            return
        if name == "启动页":
            return
        if name in self._categories:
            return
        self._categories.append(name)
        self._new_cat_input.clear()
        self._refresh_cat_list()
        self._refresh_library_entry_combo()
        self.categories_changed.emit(list(self._categories))

    def _remove_category(self, name: str):
        if name in FIXED_CATEGORIES:
            return
        if name in self._categories:
            self._categories.remove(name)
        self._refresh_cat_list()
        self._refresh_library_entry_combo()
        self.categories_changed.emit(list(self._categories))

    def _on_privacy_toggled(self, checked: bool):
        self._privacy_mode = checked
        self.privacy_mode_changed.emit(checked)

    def _on_frameless_toggled(self, checked: bool):
        self._frameless_mode = checked
        self.frameless_mode_changed.emit(checked)

    def _on_theme_changed(self, name: str):
        self._default_theme = name
        self.theme_changed.emit(name)

    def _on_startup_page_changed(self, index: int):
        page = self.startup_page_combo.itemData(index)
        if page:
            self._startup_page = page
            self.startup_page_changed.emit(page)

    def _on_library_entry_category_changed(self, index: int):
        category = self.library_entry_combo.itemData(index)
        if category:
            self._library_entry_category = category
            self.library_entry_category_changed.emit(category)

    def _change_game_dir(self):
        start = self.game_dir_input.text() or ""
        path = QFileDialog.getExistingDirectory(self, "选择默认游戏库目录", start)
        if path:
            self.game_dir_input.setText(path)
            self._sync_game_dir_input()

    def _sync_game_dir_input(self):
        path = self.game_dir_input.text().strip()
        if path == self._default_game_dir:
            return
        self._default_game_dir = path
        self.game_dir_changed.emit(path)

    def done(self, result: int):
        self._sync_game_dir_input()
        super().done(result)
