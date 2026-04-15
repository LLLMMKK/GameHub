"""搜索与选取对话框 - 粘贴图片URL或文本即可设为封面/介绍"""
import os
import tempfile
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTextEdit, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QPixmap

from utils.file_utils import save_cover


class ImageDownloader(QThread):
    """后台下载图片线程"""
    finished = pyqtSignal(bool, bytes)  # success, data

    def __init__(self, url: str):
        super().__init__()
        self._url = url

    def run(self):
        try:
            from urllib.request import urlopen, Request
            req = Request(self._url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            with urlopen(req, timeout=15) as resp:
                data = resp.read()
            self.finished.emit(True, data)
        except Exception as e:
            print(f"Download error: {e}")
            self.finished.emit(False, b"")


class WebSearchDialog(QDialog):
    """搜索与选取对话框 - 通过外部浏览器搜索，粘贴 URL/文本选取封面和介绍"""

    cover_selected = pyqtSignal(str)   # 封面路径
    desc_selected = pyqtSignal(str)    # 介绍文本

    def __init__(self, game_name: str, data_dir: str, game_id: str, parent=None):
        super().__init__(parent)
        self._game_name = game_name
        self._data_dir = data_dir
        self._game_id = game_id
        self._downloader = None
        self._cached_pixmap = None  # 缓存已下载的图片
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle(f"搜索与选取: {self._game_name}")
        self.setMinimumWidth(560)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 20)

        import webbrowser
        from urllib.parse import quote

        # === 图片搜索 ===
        img_header = QLabel("图片搜索")
        img_header.setObjectName("dialog-title")
        img_header.setStyleSheet("font-size: 18px; font-weight: bold; color: #e8edf3;")
        layout.addWidget(img_header)

        hint1 = QLabel("点击下方按钮在浏览器中搜索图片，然后回来粘贴图片链接")
        hint1.setStyleSheet("color: #4a6080; font-size: 12px;")
        layout.addWidget(hint1)

        img_row1 = QHBoxLayout()
        img_row1.setSpacing(10)

        for label, url in [
            ("🔍 百度图片", f"https://image.baidu.com/search/index?tn=baiduimage&word={quote(self._game_name + ' 游戏封面')}"),
            ("🖼 Bing图片", f"https://www.bing.com/images/search?q={quote(self._game_name + ' game cover')}"),
            ("📸 Google图片", f"https://www.google.com/search?tbm=isch&q={quote(self._game_name + ' game cover')}"),
        ]:
            btn = QPushButton(label)
            btn.setObjectName("search-engine-btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                #search-engine-btn {
                    background-color: #141c28; border: 1px solid #1e2d3d;
                    border-radius: 8px; padding: 9px 14px; color: #8fa3b8; font-size: 12px;
                }
                #search-engine-btn:hover { background-color: #1a2a3e; border-color: #3a7bd5; color: #ffffff; }
            """)
            btn.clicked.connect(lambda checked, u=url: webbrowser.open(u))
            img_row1.addWidget(btn)

        layout.addLayout(img_row1)

        # 粘贴图片URL
        url_row = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("粘贴图片 URL (如 https://...)")
        self.url_input.setStyleSheet("font-size: 12px;")
        url_row.addWidget(self.url_input, 1)

        preview_btn = QPushButton("预览")
        preview_btn.setObjectName("secondary-btn")
        preview_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        preview_btn.clicked.connect(self._preview_image)
        url_row.addWidget(preview_btn)

        use_cover_btn = QPushButton("选为封面")
        use_cover_btn.setObjectName("primary-btn")
        use_cover_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        use_cover_btn.clicked.connect(self._use_as_cover)
        url_row.addWidget(use_cover_btn)

        layout.addLayout(url_row)

        # 图片预览
        self.cover_preview = QLabel()
        self.cover_preview.setFixedSize(160, 210)
        self.cover_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_preview.setStyleSheet("background-color: #141c28; border-radius: 8px; color: #4a6080; font-size: 11px;")
        self.cover_preview.setText("图片预览区")
        self.cover_preview.hide()

        preview_row = QHBoxLayout()
        preview_row.addStretch()
        preview_row.addWidget(self.cover_preview)
        preview_row.addStretch()
        layout.addLayout(preview_row)

        # 下载状态
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #3a7bd5; font-size: 11px;")
        layout.addWidget(self._status_label)

        # 分隔线
        div1 = QFrame()
        div1.setObjectName("divider")
        div1.setFixedHeight(1)
        layout.addWidget(div1)

        # === 文本搜索 ===
        txt_header = QLabel("文本搜索")
        txt_header.setObjectName("dialog-title")
        txt_header.setStyleSheet("font-size: 18px; font-weight: bold; color: #e8edf3;")
        layout.addWidget(txt_header)

        hint2 = QLabel("点击下方按钮在浏览器中搜索，然后回来粘贴游戏介绍文本")
        hint2.setStyleSheet("color: #4a6080; font-size: 12px;")
        layout.addWidget(hint2)

        txt_row1 = QHBoxLayout()
        txt_row1.setSpacing(10)

        for label, url in [
            ("🌐 百度", f"https://www.baidu.com/s?wd={quote(self._game_name + ' 游戏 介绍')}"),
            ("🌐 Bing", f"https://www.bing.com/search?q={quote(self._game_name + ' game intro')}"),
            ("🌐 Google", f"https://www.google.com/search?q={quote(self._game_name + ' game wiki')}"),
            ("📖 维基百科", f"https://zh.wikipedia.org/wiki/Special:Search/{quote(self._game_name)}"),
        ]:
            btn = QPushButton(label)
            btn.setObjectName("search-engine-btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                #search-engine-btn {
                    background-color: #141c28; border: 1px solid #1e2d3d;
                    border-radius: 8px; padding: 9px 14px; color: #8fa3b8; font-size: 12px;
                }
                #search-engine-btn:hover { background-color: #1a2a3e; border-color: #3a7bd5; color: #ffffff; }
            """)
            btn.clicked.connect(lambda checked, u=url: webbrowser.open(u))
            txt_row1.addWidget(btn)

        layout.addLayout(txt_row1)

        # 第二行：游戏特化搜索
        txt_row2 = QHBoxLayout()
        txt_row2.setSpacing(10)

        for label, url in [
            ("🎮 Steam", f"https://store.steampowered.com/search/?term={quote(self._game_name)}"),
            ("📰 游民星空", f"https://so.gamersky.com/all?keyword={quote(self._game_name)}"),
            ("📕 百度百科", f"https://baike.baidu.com/item/{quote(self._game_name)}"),
        ]:
            btn = QPushButton(label)
            btn.setObjectName("search-engine-btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                #search-engine-btn {
                    background-color: #141c28; border: 1px solid #1e2d3d;
                    border-radius: 8px; padding: 9px 14px; color: #8fa3b8; font-size: 12px;
                }
                #search-engine-btn:hover { background-color: #1a2a3e; border-color: #3a7bd5; color: #ffffff; }
            """)
            btn.clicked.connect(lambda checked, u=url: webbrowser.open(u))
            txt_row2.addWidget(btn)

        txt_row2.addStretch()
        layout.addLayout(txt_row2)

        # 粘贴介绍文本
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("粘贴或输入游戏介绍...")
        self.desc_input.setMaximumHeight(120)
        layout.addWidget(self.desc_input)

        desc_row = QHBoxLayout()
        desc_row.addStretch()

        paste_btn = QPushButton("粘贴剪贴板")
        paste_btn.setObjectName("secondary-btn")
        paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        paste_btn.clicked.connect(self._paste_clipboard)
        desc_row.addWidget(paste_btn)

        use_desc_btn = QPushButton("选为介绍")
        use_desc_btn.setObjectName("primary-btn")
        use_desc_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        use_desc_btn.clicked.connect(self._use_as_desc)
        desc_row.addWidget(use_desc_btn)

        layout.addLayout(desc_row)

        # 关闭
        layout.addSpacing(8)
        close_row = QHBoxLayout()
        close_row.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.setObjectName("secondary-btn")
        close_btn.clicked.connect(self.close)
        close_row.addWidget(close_btn)
        layout.addLayout(close_row)

    def _preview_image(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "提示", "请先输入图片 URL")
            return
        self._status_label.setText("正在加载图片...")
        self._download_and_show(url, preview_only=True)

    def _use_as_cover(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "提示", "请先输入图片 URL")
            return
        # 如果已有缓存的图片且URL未变，直接打开裁剪对话框
        if self._cached_pixmap and not self._cached_pixmap.isNull():
            self._open_crop_dialog(self._cached_pixmap)
        else:
            self._status_label.setText("正在下载封面...")
            self._download_and_show(url, preview_only=False)

    def _download_and_show(self, url: str, preview_only: bool = False):
        if self._downloader and self._downloader.isRunning():
            self._downloader.quit()
        self._downloader = ImageDownloader(url)
        self._downloader.finished.connect(lambda ok, data: self._on_image_downloaded(ok, data, preview_only))
        self._downloader.start()

    def _on_image_downloaded(self, ok: bool, data: bytes, preview_only: bool):
        self._status_label.setText("")
        if not ok or not data:
            self._status_label.setText("下载失败，请检查 URL")
            return

        pixmap = QPixmap()
        pixmap.loadFromData(data)
        if pixmap.isNull():
            self._status_label.setText("无法识别该图片")
            return

        # 缓存图片
        self._cached_pixmap = pixmap

        if preview_only:
            scaled = pixmap.scaled(160, 210, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                   Qt.TransformationMode.SmoothTransformation)
            self.cover_preview.setPixmap(scaled)
            self.cover_preview.show()
            self._status_label.setText("预览加载成功，点击「选为封面」裁剪并确认")
        else:
            # 下载完成后打开裁剪对话框
            self._open_crop_dialog(pixmap)

    def _open_crop_dialog(self, pixmap: QPixmap):
        """打开裁剪对话框，确认后保存封面"""
        from ui.crop_dialog import CoverCropDialog
        dlg = CoverCropDialog(pixmap, self)
        if dlg.exec() == CoverCropDialog.DialogCode.Accepted:
            cropped = dlg.get_cropped_pixmap()
            if cropped and not cropped.isNull():
                tmp_path = os.path.join(tempfile.gettempdir(), f"gh_cover_{self._game_id}.jpg")
                cropped.save(tmp_path, "JPG", 90)
                cover_path = save_cover(tmp_path, self._game_id, self._data_dir)
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
                self.cover_selected.emit(cover_path)
                QMessageBox.information(self, "封面已选取", "封面图片已保存！")

    def _paste_clipboard(self):
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.desc_input.setPlainText(text)
        else:
            QMessageBox.warning(self, "提示", "剪贴板中没有文本")

    def _use_as_desc(self):
        text = self.desc_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请先输入或粘贴游戏介绍")
            return
        self.desc_selected.emit(text)
        QMessageBox.information(self, "介绍已选取", "游戏介绍已保存！")

    def closeEvent(self, event):
        if self._downloader and self._downloader.isRunning():
            self._downloader.quit()
            self._downloader.wait(3000)
        super().closeEvent(event)
