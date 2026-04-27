"""添加/编辑游戏对话框"""
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QTextEdit, QPushButton,
    QFileDialog, QFormLayout, QMessageBox, QCheckBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

from core.game_model import Game, GameDataStore
from ui.game_card import generate_default_cover
from utils.file_utils import get_cover_dir, save_cover


class AddGameDialog(QDialog):
    """添加或编辑游戏"""

    def __init__(self, store: GameDataStore, game: Game = None, default_category: str = "其他", parent=None):
        super().__init__(parent)
        self.store = store
        self.game = game  # 如果为 None 则是添加，否则是编辑
        self._default_category = default_category
        self._cover_path = ""
        self._setup_ui()
        if game:
            self._load_game(game)

    def _setup_ui(self):
        self.setWindowTitle("编辑游戏" if self.game else "添加游戏")
        self.setMinimumWidth(480)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # 标题
        title = QLabel("编辑游戏" if self.game else "添加游戏")
        title.setObjectName("dialog-title")
        layout.addWidget(title)

        # 表单
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # 游戏名称
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("输入游戏名称")
        form.addRow("游戏名称:", self.name_input)

        # 可执行文件
        exe_row = QHBoxLayout()
        self.exe_input = QLineEdit()
        self.exe_input.setPlaceholderText("选择游戏可执行文件 (.exe/.bat/.cmd)")
        exe_btn = QPushButton("浏览...")
        exe_btn.setObjectName("file-btn")
        exe_btn.clicked.connect(self._browse_exe)
        exe_row.addWidget(self.exe_input, 1)
        exe_row.addWidget(exe_btn)
        form.addRow("可执行文件:", exe_row)

        # 启动参数
        self.args_input = QLineEdit()
        self.args_input.setPlaceholderText("可选，如 -windowed -dx11")
        form.addRow("启动参数:", self.args_input)

        # 分类
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        # 跳过"全部"和"最近游玩"——它们不是可选择的分类
        self.category_combo.addItems([c for c in self.store.categories if c not in ("全部", "最近游玩")])
        self.category_combo.setCurrentText(self._default_category)
        form.addRow("分类:", self.category_combo)

        # 封面
        cover_row = QHBoxLayout()
        self.cover_preview = QLabel()
        self.cover_preview.setFixedSize(80, 100)
        self.cover_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_preview.setObjectName("cover-preview-box")
        self._update_cover_preview()

        cover_btns = QVBoxLayout()
        select_cover_btn = QPushButton("选择封面图片")
        select_cover_btn.setObjectName("file-btn")
        select_cover_btn.clicked.connect(self._browse_cover)
        clear_cover_btn = QPushButton("清除封面")
        clear_cover_btn.setObjectName("secondary-btn")
        clear_cover_btn.clicked.connect(self._clear_cover)
        cover_btns.addWidget(select_cover_btn)
        cover_btns.addWidget(clear_cover_btn)
        cover_btns.addStretch()

        cover_row.addWidget(self.cover_preview)
        cover_row.addLayout(cover_btns)
        form.addRow("封面:", cover_row)

        # 游戏介绍
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("输入游戏介绍（可选）")
        self.desc_input.setMaximumHeight(100)
        form.addRow("游戏介绍:", self.desc_input)

        # R18 标记
        self.r18_checkbox = QCheckBox("标记为 R18 游戏")
        self.r18_checkbox.setObjectName("r18-checkbox")
        form.addRow("", self.r18_checkbox)

        layout.addLayout(form)

        # 按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("secondary-btn")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.setObjectName("primary-btn")
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def _load_game(self, game: Game):
        self.name_input.setText(game.name)
        self.exe_input.setText(game.exe_path)
        self.args_input.setText(game.launch_args)
        self.category_combo.setCurrentText(game.category)
        self._cover_path = game.cover_path
        self.desc_input.setText(game.description)
        self.r18_checkbox.setChecked(game.is_r18)
        self._update_cover_preview()

    def _browse_exe(self):
        start_dir = ""
        if self.game and self.game.exe_path:
            start_dir = os.path.dirname(self.game.exe_path)
        if not start_dir:
            start_dir = self.store.default_game_dir or ""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择游戏可执行文件", start_dir,
            "可执行文件 (*.exe *.bat *.cmd);;所有文件 (*.*)"
        )
        if path:
            self.exe_input.setText(path)
            if not self.name_input.text():
                self.name_input.setText(os.path.splitext(os.path.basename(path))[0])

    def _browse_cover(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择封面图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp);;所有文件 (*.*)"
        )
        if path:
            self._cover_path = path
            self._update_cover_preview()

    def _clear_cover(self):
        self._cover_path = ""
        self._update_cover_preview()

    def _update_cover_preview(self):
        if self._cover_path and os.path.exists(self._cover_path):
            pixmap = QPixmap(self._cover_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(80, 100, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                       Qt.TransformationMode.SmoothTransformation)
                self.cover_preview.setPixmap(scaled)
                return
        # 默认封面
        name = self.name_input.text() or "?"
        pixmap = generate_default_cover(name, 80, 100)
        self.cover_preview.setPixmap(pixmap)

    def _save(self):
        name = self.name_input.text().strip()
        exe_path = self.exe_input.text().strip()

        if not name:
            QMessageBox.warning(self, "提示", "请输入游戏名称")
            return
        if not exe_path:
            QMessageBox.warning(self, "提示", "请选择游戏可执行文件")
            return
        if not os.path.isfile(exe_path):
            QMessageBox.warning(self, "提示", "可执行文件不存在")
            return

        category = self.category_combo.currentText().strip() or "其他"
        args = self.args_input.text().strip()
        desc = self.desc_input.toPlainText().strip()
        is_r18 = self.r18_checkbox.isChecked()
        new_cover = self._cover_path

        if self.game:
            game = self.game
            old_cover = game.cover_path
            game.name = name
            game.exe_path = exe_path
            game.launch_args = args
            game.category = category
            game.description = desc
            game.is_r18 = is_r18

            if new_cover and new_cover != old_cover:
                from utils.file_utils import get_cover_dir, delete_cover
                cover_dir = get_cover_dir(self.store.data_dir)
                if not os.path.abspath(new_cover).startswith(os.path.abspath(cover_dir)):
                    delete_cover(game.id, self.store.data_dir)
                    new_cover = save_cover(new_cover, game.id, self.store.data_dir)
                game.cover_path = new_cover
            elif not new_cover and old_cover:
                from utils.file_utils import delete_cover
                delete_cover(game.id, self.store.data_dir)
                game.cover_path = ""
            self.store.update_game(game)
        else:
            game = Game(name=name, exe_path=exe_path, launch_args=args,
                        category=category, description=desc, is_r18=is_r18)
            if new_cover:
                game.cover_path = save_cover(new_cover, game.id, self.store.data_dir)
            self.store.add_game(game)

        if category not in self.store.categories:
            self.store.add_category(category)

        self.accept()
