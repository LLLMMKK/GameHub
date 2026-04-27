"""侧边栏 - 分类导航和搜索（精美版）"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QHBoxLayout, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal


class CategoryButton(QWidget):
    """分类行：左侧 accent rail + 名称 + 数量胶囊"""
    clicked_category = pyqtSignal(str)

    def __init__(self, text: str, count: int = 0):
        super().__init__()
        self.category_name = text
        self.setObjectName("category-row")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._selected = False
        self._setup_ui()
        self.update_count(count)

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 7, 10, 7)
        layout.setSpacing(10)

        self._rail = QFrame()
        self._rail.setObjectName("category-rail")
        self._rail.setFixedSize(3, 18)
        layout.addWidget(self._rail)

        self._name_label = QLabel(self.category_name)
        self._name_label.setObjectName("category-name")
        self._name_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._name_label, 1)

        self._count_label = QLabel()
        self._count_label.setObjectName("category-count")
        self._count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._count_label)

    def set_selected(self, selected: bool):
        self._selected = selected
        self.setProperty("selected", str(selected).lower())
        for widget in (self, self._rail, self._name_label, self._count_label):
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def update_count(self, count: int):
        self._count_label.setVisible(count > 0)
        self._count_label.setText(str(count))

    def set_running(self, running: bool):
        self.setProperty("running", str(running).lower())
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked_category.emit(self.category_name)
        super().mousePressEvent(event)


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
        self.search_box.setPlaceholderText("搜索游戏...")
        self.search_box.textChanged.connect(self._on_search)
        layout.addWidget(self.search_box)

        layout.addSpacing(10)

        # 分隔线
        divider = QFrame()
        divider.setObjectName("divider")
        divider.setFixedHeight(1)
        layout.addWidget(divider)

        layout.addSpacing(8)

        # 分类标签
        cat_header = QLabel("  分  类")
        cat_header.setObjectName("sidebar-section-label")
        layout.addWidget(cat_header)

        layout.addSpacing(4)

        # 分类列表
        scroll = QScrollArea()
        scroll.setObjectName("category-scroll")
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
        layout.addWidget(scroll, 1)

        # 底部版本
        version = QLabel("  v1.0.0")
        version.setObjectName("sidebar-version")
        layout.addWidget(version)

    def set_categories(self, categories: list[str], counts: dict[str, int] = None, current_category: str = "全部"):
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

        if current_category not in categories:
            current_category = "全部" if "全部" in categories else (categories[0] if categories else "")
        self._select_category(current_category)

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
