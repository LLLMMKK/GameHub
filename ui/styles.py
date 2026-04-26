"""主题系统 - 5 套完整 QSS 样式表"""
from PyQt6.QtGui import QColor

# ═══════════════════════════════════════════════════
# 主题颜色定义
# ═══════════════════════════════════════════════════

_COLORS = {
    "暗夜": {
        "bg_primary": "#0e1621",
        "bg_secondary": "#0a0e14",
        "bg_card": "#141c28",
        "bg_input": "#141c28",
        "bg_input_focus": "#162030",
        "bg_hover": "#1a2a3e",
        "bg_overlay": "#111820",
        "bg_toolbar_top": "#0e1621",
        "bg_running": "#142018",
        "bg_running_hover": "#1a2c18",
        "bg_context": "#1a2535",
        "bg_context_item": "#2a4a6a",
        "bg_tooltip": "#1a2a3e",
        "bg_tooltip_border": "#2a3f5f",
        "text_primary": "#e8edf3",
        "text_secondary": "#d1d9e6",
        "text_muted": "#4a6080",
        "text_dim": "#8fa3b8",
        "text_sidebar": "#6b7d93",
        "text_sidebar_hover": "#b0c4de",
        "text_detail_value": "#b0c4de",
        "text_btn_secondary": "#8fa3b8",
        "accent": "#3a7bd5",
        "accent_hover": "#66c0f4",
        "accent_sidebar": "#66c0f4",
        "accent_sidebar_gradient": "#1a3050",
        "accent_selection": "#3a7bd5",
        "border": "#1a2332",
        "border_hover": "#3a7bd5",
        "border_btn_secondary": "#1e2d3d",
        "border_context": "#2a4a6a",
        "scrollbar_bg": "#0e1621",
        "scrollbar_handle": "#1e2d3d",
        "green": "#3a8a28",
        "green_dark": "#2d6b1e",
        "green_hover": "#5cb040",
        "green_pressed": "#1e4f14",
        "green_glow": "rgba(58,138,40,80)",
        "green_border": "#3a8a28",
        "green_border_glow": "rgba(92,176,64,150)",
        "red": "#c0392b",
        "red_dark": "#96281b",
        "red_hover": "#e74c3c",
        "red_glow": "rgba(192,57,43,80)",
        "red_border_glow": "rgba(231,76,60,150)",
        "danger_bg_top": "#a52a2a",
        "danger_bg_bot": "#7a1a1a",
        "danger_hover_top": "#c0392b",
        "danger_hover_bot": "#a52a2a",
        "file_btn_color": "#4a6080",
        "empty_icon": "#1a2332",
        "text_on_accent": "#ffffff",
    },
    "赛博朋克": {
        "bg_primary": "#06060d",
        "bg_secondary": "#030308",
        "bg_card": "#0a0a18",
        "bg_input": "#0a0a18",
        "bg_input_focus": "#0f0f22",
        "bg_hover": "#12122a",
        "bg_overlay": "#080814",
        "bg_toolbar_top": "#06060d",
        "bg_running": "#081a10",
        "bg_running_hover": "#0c2818",
        "bg_context": "#0f0f20",
        "bg_context_item": "#1a3a2a",
        "bg_tooltip": "#0f0f20",
        "bg_tooltip_border": "#1a4a2a",
        "text_primary": "#d0ffe0",
        "text_secondary": "#b0ffd0",
        "text_muted": "#2a5a3a",
        "text_dim": "#5a9a6a",
        "text_sidebar": "#3a7a4a",
        "text_sidebar_hover": "#80d0a0",
        "text_detail_value": "#80cc9a",
        "text_btn_secondary": "#5a9a6a",
        "accent": "#00ff66",
        "accent_hover": "#33ff99",
        "accent_sidebar": "#00ff66",
        "accent_sidebar_gradient": "#0a2015",
        "accent_selection": "#00ff66",
        "border": "#1a2a20",
        "border_hover": "#00ff66",
        "border_btn_secondary": "#1a2a20",
        "border_context": "#1a4a2a",
        "scrollbar_bg": "#06060d",
        "scrollbar_handle": "#1a2a20",
        "green": "#00cc44",
        "green_dark": "#009933",
        "green_hover": "#00ff66",
        "green_pressed": "#006622",
        "green_glow": "rgba(0,255,102,60)",
        "green_border": "#00ff66",
        "green_border_glow": "rgba(0,255,102,150)",
        "red": "#ff2d55",
        "red_dark": "#cc0033",
        "red_hover": "#ff5577",
        "red_glow": "rgba(255,45,85,60)",
        "red_border_glow": "rgba(255,45,85,150)",
        "danger_bg_top": "#cc2244",
        "danger_bg_bot": "#881122",
        "danger_hover_top": "#ff2d55",
        "danger_hover_bot": "#cc2244",
        "file_btn_color": "#2a5a3a",
        "empty_icon": "#1a2a20",
        "text_on_accent": "#ffffff",
    },
    "毛玻璃": {
        "bg_primary": "#0d1117",
        "bg_secondary": "#060b10",
        "bg_card": "rgba(22,27,37,180)",
        "bg_input": "rgba(22,27,37,200)",
        "bg_input_focus": "rgba(28,35,48,220)",
        "bg_hover": "rgba(40,55,80,150)",
        "bg_overlay": "rgba(18,22,30,200)",
        "bg_toolbar_top": "#0d1117",
        "bg_running": "rgba(20,35,25,160)",
        "bg_running_hover": "rgba(28,48,32,180)",
        "bg_context": "rgba(22,28,40,220)",
        "bg_context_item": "rgba(50,70,100,180)",
        "bg_tooltip": "rgba(20,35,50,220)",
        "bg_tooltip_border": "rgba(60,90,130,150)",
        "bg_r18": "",
        "bg_cat_row": "",
        "text_primary": "#e0e8f0",
        "text_secondary": "#c8d6e5",
        "text_muted": "#556677",
        "text_dim": "#8899aa",
        "text_sidebar": "#667788",
        "text_sidebar_hover": "#aabbcc",
        "text_detail_value": "#aabbcc",
        "text_btn_secondary": "#8899aa",
        "accent": "#7b9cd0",
        "accent_hover": "#a0c0ee",
        "accent_sidebar": "#8bb8e0",
        "accent_sidebar_gradient": "rgba(60,90,130,100)",
        "accent_selection": "#7b9cd0",
        "border": "rgba(255,255,255,6)",
        "border_hover": "rgba(123,156,208,150)",
        "border_btn_secondary": "rgba(255,255,255,8)",
        "border_context": "rgba(123,156,208,100)",
        "scrollbar_bg": "#0d1117",
        "scrollbar_handle": "rgba(255,255,255,8)",
        "green": "#3a8a28",
        "green_dark": "#2d6b1e",
        "green_hover": "#5cb040",
        "green_pressed": "#1e4f14",
        "green_glow": "rgba(58,138,40,60)",
        "green_border": "#3a8a28",
        "green_border_glow": "rgba(92,176,64,120)",
        "red": "#c0392b",
        "red_dark": "#96281b",
        "red_hover": "#e74c3c",
        "red_glow": "rgba(192,57,43,60)",
        "red_border_glow": "rgba(231,76,60,120)",
        "danger_bg_top": "#a52a2a",
        "danger_bg_bot": "#7a1a1a",
        "danger_hover_top": "#c0392b",
        "danger_hover_bot": "#a52a2a",
        "file_btn_color": "#556677",
        "empty_icon": "rgba(255,255,255,6)",
        "text_on_accent": "#ffffff",
    },
    "拟物质感": {
        "bg_primary": "#1a1410",
        "bg_secondary": "#0f0c08",
        "bg_card": "#221c16",
        "bg_input": "#1e1812",
        "bg_input_focus": "#262018",
        "bg_hover": "#2c2418",
        "bg_overlay": "#1c1610",
        "bg_toolbar_top": "#1a1410",
        "bg_running": "#1a2010",
        "bg_running_hover": "#242c18",
        "bg_context": "#221c18",
        "bg_context_item": "#3a2c18",
        "bg_tooltip": "#221c18",
        "bg_tooltip_border": "#4a3a20",
        "bg_r18": "",
        "bg_cat_row": "",
        "text_primary": "#e8dcc8",
        "text_secondary": "#d8ccb8",
        "text_muted": "#5a4a30",
        "text_dim": "#8a7a60",
        "text_sidebar": "#7a6a50",
        "text_sidebar_hover": "#c8b898",
        "text_detail_value": "#c8b898",
        "text_btn_secondary": "#8a7a60",
        "accent": "#c8a050",
        "accent_hover": "#e0c070",
        "accent_sidebar": "#d8b860",
        "accent_sidebar_gradient": "#2a2010",
        "accent_selection": "#c8a050",
        "border": "#2a2018",
        "border_hover": "#c8a050",
        "border_btn_secondary": "#2a2018",
        "border_context": "#4a3a20",
        "scrollbar_bg": "#1a1410",
        "scrollbar_handle": "#2a2018",
        "green": "#5a8a20",
        "green_dark": "#4a7018",
        "green_hover": "#6a9a28",
        "green_pressed": "#3a6010",
        "green_glow": "rgba(90,138,32,50)",
        "green_border": "#6a9a28",
        "green_border_glow": "rgba(106,154,40,120)",
        "red": "#b04030",
        "red_dark": "#8a2018",
        "red_hover": "#d05040",
        "red_glow": "rgba(176,64,48,50)",
        "red_border_glow": "rgba(208,80,64,120)",
        "danger_bg_top": "#8a3020",
        "danger_bg_bot": "#6a2010",
        "danger_hover_top": "#b04030",
        "danger_hover_bot": "#8a3020",
        "file_btn_color": "#5a4a30",
        "empty_icon": "#2a2018",
        "text_on_accent": "#ffffff",
    },
    "极简白": {
        "bg_primary": "#f0f2f5",
        "bg_secondary": "#e8eaef",
        "bg_card": "#ffffff",
        "bg_input": "#f5f6f8",
        "bg_input_focus": "#ffffff",
        "bg_hover": "#e8ecf2",
        "bg_overlay": "#f8f9fa",
        "bg_toolbar_top": "#f0f2f5",
        "bg_running": "#f0faf0",
        "bg_running_hover": "#e0f4e0",
        "bg_context": "#ffffff",
        "bg_context_item": "#e0e8f0",
        "bg_tooltip": "#ffffff",
        "bg_tooltip_border": "#d0d5dc",
        "bg_r18": "",
        "bg_cat_row": "",
        "text_primary": "#2c3e50",
        "text_secondary": "#34495e",
        "text_muted": "#95a5a6",
        "text_dim": "#7f8c8d",
        "text_sidebar": "#6c7a89",
        "text_sidebar_hover": "#2c3e50",
        "text_detail_value": "#34495e",
        "text_btn_secondary": "#5a6a7a",
        "accent": "#3498db",
        "accent_hover": "#5dade2",
        "accent_sidebar": "#3498db",
        "accent_sidebar_gradient": "#e0ecf8",
        "accent_selection": "#3498db",
        "border": "#e0e3e8",
        "border_hover": "#3498db",
        "border_btn_secondary": "#d0d5dc",
        "border_context": "#c0c8d0",
        "scrollbar_bg": "#f0f2f5",
        "scrollbar_handle": "#c0c5cc",
        "green": "#0d5a30",
        "green_dark": "#094520",
        "green_hover": "#117038",
        "green_pressed": "#063018",
        "green_glow": "rgba(13,90,48,50)",
        "green_border": "#0d5a30",
        "green_border_glow": "rgba(13,90,48,100)",
        "red": "#b0302a",
        "red_dark": "#7d1f18",
        "red_hover": "#c0392b",
        "red_glow": "rgba(176,48,42,40)",
        "red_border_glow": "rgba(176,48,42,80)",
        "danger_bg_top": "#b0302a",
        "danger_bg_bot": "#7d1f18",
        "danger_hover_top": "#c0392b",
        "danger_hover_bot": "#9b271e",
        "file_btn_color": "#95a5a6",
        "empty_icon": "#d0d5dc",
        "text_on_accent": "#ffffff",
    },
}

# ═══════════════════════════════════════════════════
# QSS 模板
# ═══════════════════════════════════════════════════

_STYLE_TEMPLATE = """
/* ===== 全局 ===== */
QWidget {{
    background-color: {bg_primary};
    color: {text_secondary};
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}}

QMainWindow {{
    background-color: {bg_primary};
}}

/* ===== 侧边栏 ===== */
#sidebar {{
    background-color: {bg_secondary};
    border-right: 1px solid {border};
    min-width: 210px;
    max-width: 240px;
}}

#sidebar-title {{
    color: {accent_sidebar};
    font-size: 22px;
    font-weight: bold;
    padding: 24px 20px 8px 20px;
    letter-spacing: 1px;
}}

#sidebar-subtitle {{
    color: {text_muted};
    font-size: 11px;
    padding: 0px 20px 16px 20px;
}}

/* 搜索框 */
#search-box {{
    background-color: {bg_input};
    border: 1px solid {border_btn_secondary};
    border-radius: 8px;
    padding: 10px 14px;
    color: {text_secondary};
    font-size: 13px;
    margin: 4px 14px 8px 14px;
}}

#search-box:focus {{
    border-color: {accent};
    background-color: {bg_input_focus};
}}

#search-box::placeholder {{
    color: {text_muted};
}}

/* 分类按钮 */
#category-btn {{
    background-color: transparent;
    border: none;
    text-align: left;
    padding: 11px 18px;
    color: {text_sidebar};
    font-size: 14px;
    border-radius: 6px;
    margin: 1px 10px;
}}

#category-btn:hover {{
    background-color: {bg_card};
    color: {text_sidebar_hover};
}}

#category-btn[selected="true"] {{
    background-color: {accent_sidebar_gradient};
    color: {accent_sidebar};
    border-left: 3px solid {accent};
}}

#category-btn[running="true"] {{
    background-color: {bg_running};
    color: {green};
}}

/* ===== 顶部工具栏 ===== */
#toolbar {{
    background-color: {bg_toolbar_top};
    border-bottom: 1px solid {border};
    padding: 10px 24px;
    min-height: 52px;
}}

#category-title {{
    color: {text_primary};
    font-size: 20px;
    font-weight: bold;
}}

#game-count-badge {{
    color: {text_muted};
    font-size: 13px;
    padding-left: 8px;
}}

#toolbar-btn {{
    background-color: {bg_card};
    border: 1px solid {border_btn_secondary};
    border-radius: 8px;
    padding: 9px 18px;
    color: {text_btn_secondary};
    font-size: 13px;
}}

#toolbar-btn:hover {{
    background-color: {bg_hover};
    border-color: {accent};
    color: {text_primary};
}}

#toolbar-btn:pressed {{
    background-color: {bg_primary};
}}

/* 添加游戏按钮 */
#add-game-btn {{
    background-color: {green};
    border: 1px solid {green_border};
    border-radius: 8px;
    padding: 9px 20px;
    color: {text_on_accent};
    font-size: 13px;
    font-weight: bold;
}}

#add-game-btn:hover {{
    background-color: {green_hover};
    border-color: {green_hover};
}}

/* 无边框窗口控制按钮 */
#win-control-btn {{
    background-color: transparent;
    border: none;
    border-radius: 4px;
    color: {text_secondary};
    font-size: 14px;
    font-weight: bold;
}}

#win-control-btn:hover {{
    background-color: {bg_hover};
    color: {text_primary};
}}

#win-close-btn {{
    background-color: transparent;
    border: none;
    border-radius: 4px;
    color: {text_secondary};
    font-size: 14px;
    font-weight: bold;
}}

#win-close-btn:hover {{
    background-color: #c0392b;
    color: #ffffff;
}}

/* 排序下拉框 */
#sort-combo {{
    background-color: {bg_card};
    border: 1px solid {border_btn_secondary};
    border-radius: 6px;
    padding: 6px 10px;
    color: {text_btn_secondary};
    font-size: 12px;
    min-width: 90px;
}}

#sort-combo:hover {{
    border-color: {accent};
}}

#sort-combo QAbstractItemView {{
    background-color: {bg_card};
    border: 1px solid {border_btn_secondary};
    color: {text_secondary};
    selection-background-color: {bg_hover};
}}

#sort-label {{
    color: {text_muted};
    font-size: 12px;
}}

/* 返回按钮 */
#back-btn {{
    background: transparent;
    border: none;
    color: {accent};
    font-size: 14px;
    padding: 6px 0px;
}}

#back-btn:hover {{
    color: {accent_hover};
}}

/* 右键菜单 */
#card-context-menu {{
    background-color: {bg_context};
    border: 1px solid {border_context};
    border-radius: 6px;
    padding: 4px;
}}

#card-context-menu::item {{
    color: {text_primary};
    padding: 6px 24px;
    border-radius: 4px;
}}

#card-context-menu::item:selected {{
    background-color: {bg_context_item};
}}

/* 详情信息值 */
#detail-info-value {{
    color: {text_detail_value};
    font-size: 14px;
    background: transparent;
    padding-left: 4px;
}}

/* ===== 游戏卡片 ===== */
#game-card {{
    background-color: {bg_card};
    border-radius: 10px;
    border: 1px solid {border};
    padding: 24px 20px 8px 20px;
}}

#game-card:hover {{
    border-color: {accent};
    background-color: {bg_hover};
}}

#game-card[running="true"] {{
    border-color: {green_border};
    background-color: {bg_running};
}}

#game-card[running="true"]:hover {{
    border-color: {green_hover};
    background-color: {bg_running_hover};
}}

#game-card[selected="true"] {{
    border-color: {accent};
}}

#game-cover {{
    background-color: {bg_secondary};
    border-radius: 9px 9px 0 0;
}}

#game-title {{
    color: {text_primary};
    font-size: 13px;
    font-weight: bold;
    padding: 8px 10px 2px 10px;
}}

#game-time {{
    color: {text_muted};
    font-size: 11px;
    padding: 0px 10px 6px 10px;
}}

#card-cat-tag {{
    color: {accent};
    background-color: {bg_card};
    border: 1px solid {border_btn_secondary};
    border-radius: 3px;
    padding: 1px 6px;
    font-size: 10px;
}}

#card-r18-tag {{
    color: #ff4444;
    background-color: #2a0a0a;
    border: 1px solid #ff4444;
    border-radius: 3px;
    padding: 1px 5px;
    font-size: 9px;
    font-weight: bold;
}}

/* 卡片内播放按钮 */
#card-play-btn {{
    background-color: {green};
    border: none;
    border-radius: 12px;
    color: {text_on_accent};
    font-weight: bold;
    font-size: 11px;
    padding: 24px 20px 8px 20px;
}}

#card-play-btn:hover {{
    background-color: {green_hover};
}}

#card-play-btn:pressed {{
    background-color: {green_pressed};
}}

#card-play-btn[running="true"] {{
    background-color: {red};
}}

#card-play-btn[running="true"]:hover {{
    background-color: {red_hover};
}}

/* 悬浮遮罩大播放按钮 */
#card-play-overlay-btn {{
    background-color: {green};
    border: 2px solid {green_border_glow};
    border-radius: 28px;
    color: {text_on_accent};
    font-weight: bold;
    font-size: 22px;
}}

#card-play-overlay-btn:hover {{
    background-color: {green_hover};
    border-color: {green_border_glow};
}}

#card-play-overlay-btn:pressed {{
    background-color: {green_pressed};
}}

#card-play-overlay-btn[running="true"] {{
    background-color: {red};
    border-color: {red_border_glow};
}}

#card-play-overlay-btn[running="true"]:hover {{
    background-color: {red_hover};
}}

/* 详情面板播放按钮 */
#play-btn {{
    background-color: {green};
    border: none;
    border-radius: 10px;
    color: {text_on_accent};
    font-weight: bold;
    font-size: 15px;
    padding: 12px 24px;
}}

#play-btn:hover {{
    background-color: {green_hover};
}}

#play-btn:pressed {{
    background-color: {green_pressed};
}}

#play-btn[running="true"] {{
    background-color: {red};
}}

#play-btn[running="true"]:hover {{
    background-color: {red_hover};
}}

/* ===== 滚动条 ===== */
QScrollBar:vertical {{
    background-color: {scrollbar_bg};
    width: 6px;
    border: none;
    margin: 4px 2px;
}}

QScrollBar::handle:vertical {{
    background-color: {scrollbar_handle};
    border-radius: 3px;
    min-height: 40px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {accent};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    background-color: {scrollbar_bg};
    height: 6px;
    border: none;
    margin: 2px 4px;
}}

QScrollBar::handle:horizontal {{
    background-color: {scrollbar_handle};
    border-radius: 3px;
    min-width: 40px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {accent};
}}

/* ===== 对话框 ===== */
QDialog {{
    background-color: {bg_primary};
}}

#dialog-title {{
    color: {text_primary};
    font-size: 22px;
    font-weight: bold;
    padding-bottom: 16px;
}}

/* 输入框 */
QLineEdit, QTextEdit {{
    background-color: {bg_input};
    border: 1px solid {border_btn_secondary};
    border-radius: 8px;
    padding: 10px 14px;
    color: {text_secondary};
    selection-background-color: {accent_selection};
}}

QLineEdit:focus, QTextEdit:focus {{
    border-color: {accent};
    background-color: {bg_input_focus};
}}

/* 下拉框 */
QComboBox {{
    background-color: {bg_input};
    border: 1px solid {border_btn_secondary};
    border-radius: 8px;
    padding: 10px 14px;
    color: {text_secondary};
}}

QComboBox:hover {{
    border-color: {accent};
}}

QComboBox::drop-down {{
    border: none;
    width: 30px;
}}

QComboBox QAbstractItemView {{
    background-color: {bg_input};
    border: 1px solid {border_btn_secondary};
    color: {text_secondary};
    selection-background-color: {bg_hover};
    border-radius: 6px;
    outline: none;
}}

/* ===== 按钮样式 ===== */
QPushButton#primary-btn {{
    background-color: {green};
    border: none;
    border-radius: 8px;
    color: {text_on_accent};
    font-weight: bold;
    padding: 11px 28px;
    font-size: 14px;
}}

QPushButton#primary-btn:hover {{
    background-color: {green_hover};
}}

QPushButton#secondary-btn {{
    background-color: {bg_card};
    border: 1px solid {border_btn_secondary};
    border-radius: 8px;
    color: {text_btn_secondary};
    padding: 11px 28px;
    font-size: 14px;
}}

QPushButton#secondary-btn:hover {{
    background-color: {bg_hover};
    border-color: {accent};
    color: {text_primary};
}}

QPushButton#danger-btn {{
    background-color: {danger_bg_top};
    border: none;
    border-radius: 8px;
    color: {text_on_accent};
    padding: 11px 28px;
    font-size: 14px;
}}

QPushButton#danger-btn:hover {{
    background-color: {danger_hover_top};
}}

/* 标签 */
QLabel#section-label {{
    color: {text_muted};
    font-size: 11px;
    letter-spacing: 1px;
    padding-bottom: 4px;
}}

/* ===== 详情面板 ===== */
#detail-panel {{
    background-color: {bg_secondary};
    border-left: 1px solid {border};
}}

#detail-title {{
    color: {text_primary};
    font-size: 32px;
    font-weight: bold;
    background: transparent;
}}

#detail-r18-tag {{
    color: #ff4444;
    background-color: #2a0a0a;
    border: 1px solid #ff4444;
    border-radius: 4px;
    padding: 2px 10px;
    font-size: 12px;
    font-weight: bold;
}}

#detail-info {{
    color: {text_muted};
    font-size: 12px;
}}

#settings-section-title {{
    color: {text_primary};
    font-size: 15px;
    font-weight: bold;
    background: transparent;
}}

#settings-cat-label {{
    color: {text_secondary};
    font-size: 13px;
    background: transparent;
}}

#detail-category-tag {{
    color: {accent};
    font-size: 12px;
    background-color: {bg_card};
    border: 1px solid {border_btn_secondary};
    border-radius: 4px;
    padding: 2px 10px;
}}

/* ===== 游戏详情页 ===== */
#detail-root {{
    background-color: {bg_primary};
}}

#detail-cover {{
    background-color: {bg_card};
    border-radius: 12px;
    border: 1px solid {border};
}}

#desc-card {{
    background-color: {bg_overlay};
    border: 1px solid {border};
    border-radius: 10px;
    padding: 20px;
}}

#desc-title {{
    color: {text_dim};
    font-size: 14px;
    font-weight: bold;
    background: transparent;
    padding-bottom: 10px;
}}

#desc-content {{
    background-color: {bg_primary};
    border: none;
    color: {text_detail_value};
    font-size: 14px;
    selection-background-color: {accent_selection};
}}

#info-key {{
    color: {text_muted};
    font-size: 11px;
    background: transparent;
}}

#info-value {{
    color: {text_detail_value};
    font-size: 13px;
    background: transparent;
}}

#section-header {{
    color: {text_muted};
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
    background: transparent;
}}

/* 空状态 */
#empty-hint {{
    color: {text_muted};
    font-size: 18px;
}}

#empty-icon {{
    color: {empty_icon};
    font-size: 64px;
}}

/* 分隔线 */
#divider {{
    background-color: {border};
    max-height: 1px;
}}

/* 文件选择按钮 */
QPushButton#file-btn {{
    background-color: {bg_card};
    border: 1px dashed {border_btn_secondary};
    border-radius: 8px;
    color: {file_btn_color};
    padding: 12px;
}}

QPushButton#file-btn:hover {{
    border-color: {accent};
    color: {text_dim};
    background-color: {bg_input_focus};
}}

/* 列表项 */
QListWidget {{
    background-color: transparent;
    border: none;
    outline: none;
}}

QListWidget::item {{
    padding: 6px;
    border-radius: 4px;
}}

QListWidget::item:hover {{
    background-color: {bg_card};
}}

QListWidget::item:selected {{
    background-color: {bg_hover};
}}

/* 标签页 */
QTabWidget::pane {{
    border: none;
    background-color: {bg_primary};
}}

QTabBar::tab {{
    background-color: {bg_secondary};
    color: {text_muted};
    padding: 10px 20px;
    border: none;
    border-bottom: 2px solid transparent;
}}

QTabBar::tab:selected {{
    color: {text_primary};
    border-bottom: 2px solid {accent};
}}

QTabBar::tab:hover {{
    color: {text_dim};
}}

/* QMessageBox */
QMessageBox {{
    background-color: {bg_primary};
}}

QMessageBox QLabel {{
    color: {text_secondary};
    background-color: transparent;
}}

QMessageBox QPushButton {{
    background-color: {bg_card};
    border: 1px solid {border_btn_secondary};
    border-radius: 6px;
    color: {text_secondary};
    padding: 8px 20px;
    min-width: 80px;
}}

QMessageBox QPushButton:hover {{
    background-color: {bg_hover};
    border-color: {accent};
}}

/* Tooltip */
QToolTip {{
    background-color: {bg_tooltip};
    color: {text_secondary};
    border: 1px solid {bg_tooltip_border};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}
"""

# ═══════════════════════════════════════════════════
# 生成所有主题
# ═══════════════════════════════════════════════════

def _build_style(colors: dict) -> str:
    """根据颜色方案生成 QSS，额外覆盖需要多层格式化的样式"""
    style = _STYLE_TEMPLATE.format(**colors)
    return style

THEMES = {name: _build_style(colors) for name, colors in _COLORS.items()}
DARK_STYLE = THEMES["暗夜"]
