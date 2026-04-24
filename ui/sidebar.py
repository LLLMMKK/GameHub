"""侧边栏 - 分类导航和搜索（精美版）"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal


# 分类图标映射
CATEGORY_ICONS = {
    "全部": "🎮", "最近游玩": "🕐", "动作": "⚔", "策略": "🧠",
    "RPG": "🗡", "冒险": "🗺", "模拟": "🏗", "体育": "⚽",
    "竞速": "🏎", "休闲": "☕", "其他": "📁",
}


class CategoryButton(QPushButton):
    """分类按钮"""
    clicked_category = pyqtSignal(str)

    def __init__(self, text: str, count: int = 0):
        super().__init__()
        self.category_name = text
        self.setObjectName("category-btn")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._selected = False
        self._update_text(text, count)
        self.clicked.connect(lambda: self.clicked_category.emit(text))

    def _update_text(self, text: str, count: int = 0):
        icon = CATEGORY_ICONS.get(text, "📂")
        display = f"  {icon}  {text}"
        if count > 0:
            display += f"  ({count})"
        self.setText(display)

    def set_selected(self, selected: bool):
        self._selected = selected
        self.setProperty("selected", str(selected).lower())
        self.style().unpolish(self)
        self.style().polish(self)

    def update_count(self, count: int):
        self._update_text(self.category_name, count)

    def set_running(self, running: bool):
        self.setProperty("running", str(running).lower())
        self.style().unpolish(self)
        self.style().polish(self)


class Sidebar(QWidget):
    """侧边栏导航"""
    category_changed = pyqtSignal(str)
    search_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self._current_category = "全部"
        self._buttons: list[CategoryButton] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo / 标题
        title = QLabel("  GameHub")
        title.setObjectName("sidebar-title")
        layout.addWidget(title)

        # 副标题
        subtitle = QLabel("  本地游戏管理器")
        subtitle.setObjectName("sidebar-subtitle")
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        # 搜索框
        self.search_box = QLineEdit()
        self.search_box.setObjectName("search-box")
        self.search_box.setPlaceholderText("🔍  搜索游戏...")
        self.search_box.textChanged.connect(self._on_search)
        layout.addWidget(self.search_box)

        layout.addSpacing(16)

        # 分隔线
        divider = QFrame()
        divider.setObjectName("divider")
        divider.setFixedHeight(1)
        layout.addWidget(divider)

        layout.addSpacing(12)

        # 分类标签
        cat_header = QLabel("  分  类")
        cat_header.setStyleSheet(
            "color: #3d5a80; font-size: 11px; font-weight: bold; "
            "padding: 2px 18px; letter-spacing: 3px; background: transparent;"
        )
        layout.addWidget(cat_header)

        layout.addSpacing(4)

        # 分类列表
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self._cat_container = QWidget()
        self._cat_container.setStyleSheet("background: transparent;")
        self._cat_layout = QVBoxLayout(self._cat_container)
        self._cat_layout.setContentsMargins(0, 0, 0, 0)
        self._cat_layout.setSpacing(1)
        self._cat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self._cat_container)
        layout.addWidget(scroll)

        # 底部版本
        layout.addStretch()
        version = QLabel("  v1.0.0")
        version.setStyleSheet("color: #3d5a80; font-size: 10px; padding: 8px 18px; background: transparent;")
        layout.addWidget(version)

    def set_categories(self, categories: list[str], counts: dict[str, int] = None):
        if counts is None:
            counts = {}

        for btn in self._buttons:
            self._cat_layout.removeWidget(btn)
            btn.deleteLater()
        self._buttons.clear()

        for cat in categories:
            count = counts.get(cat, 0)
            btn = CategoryButton(cat, count)
            btn.clicked_category.connect(self._on_category_click)
            self._cat_layout.addWidget(btn)
            self._buttons.append(btn)

        self._select_category("全部")

    def update_counts(self, counts: dict[str, int]):
        for btn in self._buttons:
            btn.update_count(counts.get(btn.category_name, 0))

    def _on_category_click(self, category: str):
        self._select_category(category)
        self.category_changed.emit(category)

    def _select_category(self, category: str):
        self._current_category = category
        for btn in self._buttons:
            btn.set_selected(btn.category_name == category)

    def _on_search(self, text: str):
        self.search_changed.emit(text.strip())

    def current_category(self) -> str:
        return self._current_category
