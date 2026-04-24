"""深色主题 QSS 样式表 - 精美现代风格"""

DARK_STYLE = """
/* ===== 全局 ===== */
QWidget {
    background-color: #0e1621;
    color: #d1d9e6;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #0e1621;
}

/* ===== 侧边栏 ===== */
#sidebar {
    background-color: #0a0e14;
    border-right: 1px solid #1a2332;
    min-width: 210px;
    max-width: 240px;
}

#sidebar-title {
    color: #66c0f4;
    font-size: 22px;
    font-weight: bold;
    padding: 24px 20px 8px 20px;
    letter-spacing: 1px;
}

#sidebar-subtitle {
    color: #3d5a80;
    font-size: 11px;
    padding: 0px 20px 16px 20px;
}

/* 搜索框 */
#search-box {
    background-color: #141c28;
    border: 1px solid #1e2d3d;
    border-radius: 8px;
    padding: 10px 14px;
    color: #d1d9e6;
    font-size: 13px;
    margin: 4px 14px 8px 14px;
}

#search-box:focus {
    border-color: #3a7bd5;
    background-color: #162030;
}

#search-box::placeholder {
    color: #3d5a80;
}

/* 分类按钮 */
#category-btn {
    background-color: transparent;
    border: none;
    text-align: left;
    padding: 11px 18px;
    color: #6b7d93;
    font-size: 14px;
    border-radius: 6px;
    margin: 1px 10px;
}

#category-btn:hover {
    background-color: #141c28;
    color: #b0c4de;
}

#category-btn[selected="true"] {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1a3050, stop:1 #0e1621);
    color: #66c0f4;
    border-left: 3px solid #3a7bd5;
}

#category-btn[running="true"] {
    background-color: #1a2510;
    color: #5c9e10;
}

/* ===== 顶部工具栏 ===== */
#toolbar {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #111922, stop:1 #0e1621);
    border-bottom: 1px solid #1a2332;
    padding: 10px 24px;
    min-height: 52px;
}

#category-title {
    color: #e8edf3;
    font-size: 20px;
    font-weight: bold;
}

#game-count-badge {
    color: #3d5a80;
    font-size: 13px;
    padding-left: 8px;
}

#toolbar-btn {
    background-color: #141c28;
    border: 1px solid #1e2d3d;
    border-radius: 8px;
    padding: 9px 18px;
    color: #8fa3b8;
    font-size: 13px;
}

#toolbar-btn:hover {
    background-color: #1a2a3e;
    border-color: #3a7bd5;
    color: #ffffff;
}

#toolbar-btn:pressed {
    background-color: #0e1621;
}

/* 添加游戏按钮特殊样式 */
#add-game-btn {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #2d6b1e, stop:1 #1e4f14);
    border: 1px solid #3a8a28;
    border-radius: 8px;
    padding: 9px 20px;
    color: #ffffff;
    font-size: 13px;
    font-weight: bold;
}

#add-game-btn:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #3a8a28, stop:1 #2d6b1e);
    border-color: #5cb040;
}

/* 排序下拉框 */
#sort-combo {
    background-color: #141c28;
    border: 1px solid #1e2d3d;
    border-radius: 6px;
    padding: 6px 10px;
    color: #8fa3b8;
    font-size: 12px;
    min-width: 90px;
}

#sort-combo:hover {
    border-color: #3a7bd5;
}

#sort-combo QAbstractItemView {
    background-color: #141c28;
    border: 1px solid #1e2d3d;
    color: #d1d9e6;
    selection-background-color: #1a2a3e;
}

/* 排序标签 */
#sort-label {
    color: #4a6080;
    font-size: 12px;
}

/* 返回按钮 */
#back-btn {
    background: transparent;
    border: none;
    color: #3a7bd5;
    font-size: 14px;
    padding: 6px 0px;
}

#back-btn:hover {
    color: #66c0f4;
}

/* 右键菜单 */
#card-context-menu {
    background-color: #1a2535;
    border: 1px solid #2a4a6a;
    border-radius: 6px;
    padding: 4px;
}

#card-context-menu::item {
    color: #e8edf3;
    padding: 6px 24px;
    border-radius: 4px;
}

#card-context-menu::item:selected {
    background-color: #2a4a6a;
}

/* 详情信息值 */
#detail-info-value {
    color: #b0c4de;
    font-size: 14px;
    background: transparent;
    padding-left: 4px;
}

/* ===== 游戏卡片 ===== */
#game-card {
    background-color: #141c28;
    border-radius: 10px;
    border: 1px solid #1a2332;
    padding: 0px;
}

#game-card:hover {
    border-color: #3a7bd5;
    background-color: #1a2a3e;
}

#game-card[running="true"] {
    border-color: #3a8a28;
    background-color: #142018;
}

#game-card[running="true"]:hover {
    border-color: #5cb040;
    background-color: #1a2c18;
}

#game-card[selected="true"] {
    border-color: #3a7bd5;
}

#game-cover {
    background-color: #0a0e14;
    border-radius: 9px 9px 0 0;
}

#game-title {
    color: #e8edf3;
    font-size: 13px;
    font-weight: bold;
    padding: 8px 10px 2px 10px;
}

#game-time {
    color: #4a6080;
    font-size: 11px;
    padding: 0px 10px 6px 10px;
}

/* 卡片内播放按钮 */
#card-play-btn {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #3a8a28, stop:1 #2d6b1e);
    border: none;
    border-radius: 12px;
    color: #ffffff;
    font-weight: bold;
    font-size: 11px;
    padding: 0px;
}

#card-play-btn:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #5cb040, stop:1 #3a8a28);
}

#card-play-btn:pressed {
    background-color: #1e4f14;
}

#card-play-btn[running="true"] {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #c0392b, stop:1 #96281b);
}

#card-play-btn[running="true"]:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #e74c3c, stop:1 #c0392b);
}

/* 悬浮遮罩上的大播放按钮 */
#card-play-overlay-btn {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #3a8a28, stop:1 #2d6b1e);
    border: 2px solid rgba(92, 176, 64, 150);
    border-radius: 28px;
    color: #ffffff;
    font-weight: bold;
    font-size: 22px;
}

#card-play-overlay-btn:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #5cb040, stop:1 #3a8a28);
    border-color: rgba(92, 176, 64, 200);
}

#card-play-overlay-btn:pressed {
    background-color: #1e4f14;
}

#card-play-overlay-btn[running="true"] {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #c0392b, stop:1 #96281b);
    border-color: rgba(231, 76, 60, 150);
}

#card-play-overlay-btn[running="true"]:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #e74c3c, stop:1 #c0392b);
}

/* 详情面板播放按钮 */
#play-btn {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #3a8a28, stop:1 #2d6b1e);
    border: none;
    border-radius: 10px;
    color: #ffffff;
    font-weight: bold;
    font-size: 15px;
    padding: 12px 24px;
}

#play-btn:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #5cb040, stop:1 #3a8a28);
}

#play-btn:pressed {
    background-color: #1e4f14;
}

#play-btn[running="true"] {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #c0392b, stop:1 #96281b);
}

#play-btn[running="true"]:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #e74c3c, stop:1 #c0392b);
}

/* ===== 滚动条 ===== */
QScrollBar:vertical {
    background-color: #0e1621;
    width: 6px;
    border: none;
    margin: 4px 2px;
}

QScrollBar::handle:vertical {
    background-color: #1e2d3d;
    border-radius: 3px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background-color: #3a7bd5;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    background-color: #0e1621;
    height: 6px;
    border: none;
    margin: 2px 4px;
}

QScrollBar::handle:horizontal {
    background-color: #1e2d3d;
    border-radius: 3px;
    min-width: 40px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #3a7bd5;
}

/* ===== 对话框 ===== */
QDialog {
    background-color: #0e1621;
}

#dialog-title {
    color: #e8edf3;
    font-size: 22px;
    font-weight: bold;
    padding-bottom: 16px;
}

/* 输入框 */
QLineEdit, QTextEdit {
    background-color: #141c28;
    border: 1px solid #1e2d3d;
    border-radius: 8px;
    padding: 10px 14px;
    color: #d1d9e6;
    selection-background-color: #3a7bd5;
}

QLineEdit:focus, QTextEdit:focus {
    border-color: #3a7bd5;
    background-color: #162030;
}

/* 下拉框 */
QComboBox {
    background-color: #141c28;
    border: 1px solid #1e2d3d;
    border-radius: 8px;
    padding: 10px 14px;
    color: #d1d9e6;
}

QComboBox:hover {
    border-color: #3a7bd5;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox QAbstractItemView {
    background-color: #141c28;
    border: 1px solid #1e2d3d;
    color: #d1d9e6;
    selection-background-color: #1a2a3e;
    border-radius: 6px;
    outline: none;
}

/* ===== 按钮样式 ===== */
QPushButton#primary-btn {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #3a8a28, stop:1 #2d6b1e);
    border: none;
    border-radius: 8px;
    color: #ffffff;
    font-weight: bold;
    padding: 11px 28px;
    font-size: 14px;
}

QPushButton#primary-btn:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #5cb040, stop:1 #3a8a28);
}

QPushButton#secondary-btn {
    background-color: #141c28;
    border: 1px solid #1e2d3d;
    border-radius: 8px;
    color: #8fa3b8;
    padding: 11px 28px;
    font-size: 14px;
}

QPushButton#secondary-btn:hover {
    background-color: #1a2a3e;
    border-color: #3a7bd5;
    color: #ffffff;
}

QPushButton#danger-btn {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #a52a2a, stop:1 #7a1a1a);
    border: none;
    border-radius: 8px;
    color: #ffffff;
    padding: 11px 28px;
    font-size: 14px;
}

QPushButton#danger-btn:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #c0392b, stop:1 #a52a2a);
}

/* 标签 */
QLabel#section-label {
    color: #4a6080;
    font-size: 11px;
    letter-spacing: 1px;
    padding-bottom: 4px;
}

/* ===== 详情面板 ===== */
#detail-panel {
    background-color: #0a0e14;
    border-left: 1px solid #1a2332;
}

#detail-title {
    color: #e8edf3;
    font-size: 24px;
    font-weight: bold;
}

#detail-info {
    color: #4a6080;
    font-size: 12px;
}

#detail-category-tag {
    color: #3a7bd5;
    font-size: 12px;
    background-color: #141c28;
    border: 1px solid #1e2d3d;
    border-radius: 4px;
    padding: 2px 10px;
}

/* 空状态提示 */
#empty-hint {
    color: #4a6080;
    font-size: 18px;
}

#empty-icon {
    color: #1a2332;
    font-size: 64px;
}

/* 分隔线 */
#divider {
    background-color: #1a2332;
    max-height: 1px;
}

/* 文件选择按钮 */
QPushButton#file-btn {
    background-color: #141c28;
    border: 1px dashed #1e2d3d;
    border-radius: 8px;
    color: #4a6080;
    padding: 12px;
}

QPushButton#file-btn:hover {
    border-color: #3a7bd5;
    color: #8fa3b8;
    background-color: #162030;
}

/* 列表项 */
QListWidget {
    background-color: transparent;
    border: none;
    outline: none;
}

QListWidget::item {
    padding: 6px;
    border-radius: 4px;
}

QListWidget::item:hover {
    background-color: #141c28;
}

QListWidget::item:selected {
    background-color: #1a2a3e;
}

/* 标签页 */
QTabWidget::pane {
    border: none;
    background-color: #0e1621;
}

QTabBar::tab {
    background-color: #0a0e14;
    color: #4a6080;
    padding: 10px 20px;
    border: none;
    border-bottom: 2px solid transparent;
}

QTabBar::tab:selected {
    color: #e8edf3;
    border-bottom: 2px solid #3a7bd5;
}

QTabBar::tab:hover {
    color: #8fa3b8;
}

/* QMessageBox */
QMessageBox {
    background-color: #0e1621;
}

QMessageBox QLabel {
    color: #d1d9e6;
    background-color: transparent;
}

QMessageBox QPushButton {
    background-color: #141c28;
    border: 1px solid #1e2d3d;
    border-radius: 6px;
    color: #d1d9e6;
    padding: 8px 20px;
    min-width: 80px;
}

QMessageBox QPushButton:hover {
    background-color: #1a2a3e;
    border-color: #3a7bd5;
}

/* Tooltip */
QToolTip {
    background-color: #1a2a3e;
    color: #d1d9e6;
    border: 1px solid #2a3f5f;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}
"""
