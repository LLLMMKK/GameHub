"""设置对话框"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QFormLayout, QLineEdit, QCheckBox,
    QWidget, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal


# 不可删除的分类
FIXED_CATEGORIES = {"全部", "最近游玩"}


class SettingsDialog(QDialog):
    """应用设置"""

    privacy_mode_changed = pyqtSignal(bool)  # 隐私模式变更信号
    categories_changed = pyqtSignal()        # 分类变更信号

    def __init__(self, data_dir: str, privacy_mode: bool = False,
                 categories: list[str] = None, parent=None):
        super().__init__(parent)
        self.data_dir = data_dir
        self._privacy_mode = privacy_mode
        self._categories = list(categories) if categories else []
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("设置")
        self.setMinimumWidth(480)
        self.setMinimumHeight(400)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # 标题
        title = QLabel("设置")
        title.setObjectName("dialog-title")
        layout.addWidget(title)

        # 表单
        form = QFormLayout()
        form.setSpacing(12)

        # 数据目录
        dir_row = QHBoxLayout()
        self.dir_input = QLineEdit(self.data_dir)
        self.dir_input.setReadOnly(True)
        dir_btn = QPushButton("更改")
        dir_btn.setObjectName("file-btn")
        dir_btn.clicked.connect(self._change_dir)
        dir_row.addWidget(self.dir_input, 1)
        dir_row.addWidget(dir_btn)
        form.addRow("数据目录:", dir_row)

        # 信息
        info = QLabel("数据目录存储游戏列表、封面和统计数据。\n更改目录不会移动现有数据。")
        info.setObjectName("detail-info")
        form.addRow("", info)

        # 隐私模式
        self.privacy_checkbox = QCheckBox("启用隐私模式")
        self.privacy_checkbox.setChecked(self._privacy_mode)
        self.privacy_checkbox.setStyleSheet("color: #e8edf3; font-size: 13px;")
        self.privacy_checkbox.toggled.connect(self._on_privacy_toggled)
        form.addRow("", self.privacy_checkbox)

        privacy_info = QLabel("开启后，R18 游戏的封面将被打马赛克，名称将被遮蔽")
        privacy_info.setObjectName("detail-info")
        privacy_info.setStyleSheet("color: #4a6080; font-size: 11px;")
        form.addRow("", privacy_info)

        layout.addLayout(form)

        # 分隔线
        div = QFrame()
        div.setObjectName("divider")
        div.setFixedHeight(1)
        layout.addWidget(div)

        # 分类管理区域
        cat_header = QLabel("分类管理")
        cat_header.setStyleSheet(
            "color: #e8edf3; font-size: 15px; font-weight: bold; background: transparent;"
        )
        layout.addWidget(cat_header)

        cat_info = QLabel("添加或删除游戏分类。删除分类后，该分类下的游戏将归入「其他」。")
        cat_info.setStyleSheet("color: #4a6080; font-size: 11px; background: transparent;")
        cat_info.setWordWrap(True)
        layout.addWidget(cat_info)

        # 分类列表（滚动区域）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll.setMaximumHeight(200)

        self._cat_list_widget = QWidget()
        self._cat_list_widget.setStyleSheet("background: transparent;")
        self._cat_list_layout = QVBoxLayout(self._cat_list_widget)
        self._cat_list_layout.setContentsMargins(0, 0, 0, 0)
        self._cat_list_layout.setSpacing(2)
        self._cat_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self._cat_list_widget)
        layout.addWidget(scroll)

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

        # 底部按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.setObjectName("primary-btn")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

        # 填充分类列表
        self._refresh_cat_list()

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
            cat_label.setStyleSheet("color: #b0c4de; font-size: 13px; background: transparent;")

            is_fixed = cat in FIXED_CATEGORIES
            if is_fixed:
                cat_label.setStyleSheet(
                    "color: #4a6080; font-size: 13px; background: transparent;"
                )

            row_layout.addWidget(cat_label, 1)

            if not is_fixed:
                del_btn = QPushButton("删除")
                del_btn.setFixedSize(52, 26)
                del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                del_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3a1a1a;
                        border: 1px solid #5a2a2a;
                        border-radius: 4px;
                        color: #e07070;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: #5a2a2a;
                        border-color: #c0392b;
                        color: #ff8888;
                    }
                """)
                del_btn.clicked.connect(lambda checked, c=cat: self._remove_category(c))
                row_layout.addWidget(del_btn)

            self._cat_list_layout.addWidget(row)

    def _add_category(self):
        name = self._new_cat_input.text().strip()
        if not name:
            return
        if name in self._categories:
            return
        self._categories.append(name)
        self._new_cat_input.clear()
        self._refresh_cat_list()
        self.categories_changed.emit()

    def _remove_category(self, name: str):
        if name in FIXED_CATEGORIES:
            return
        if name in self._categories:
            self._categories.remove(name)
        self._refresh_cat_list()
        self.categories_changed.emit()

    def _change_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择数据目录")
        if path:
            self.dir_input.setText(path)

    def _on_privacy_toggled(self, checked: bool):
        self._privacy_mode = checked
        self.privacy_mode_changed.emit(checked)
