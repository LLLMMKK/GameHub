"""搜索与选取对话框 - 粘贴图片URL或文本即可设为封面/介绍"""
import os
import tempfile
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTextEdit, QMessageBox, QFrame,
    QWidget, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QPixmap

from ui.game_card import fit_cover_pixmap
from ui.widgets.frameless_dialog import FramelessDialogTitleBar, apply_dialog_frameless
from utils.file_utils import save_cover

class ImageDownloader(QThread):
    """后台下载图片线程"""
    downloaded = pyqtSignal(bool, bytes)  # success, data

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
                max_size = 10 * 1024 * 1024
                data = resp.read(max_size + 1)
            if len(data) > max_size:
                raise ValueError("Image is larger than 10 MB")
            self.downloaded.emit(True, data)
        except Exception as e:
            print(f"Download error: {e}")
            self.downloaded.emit(False, b"")


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
        self._cached_url = ""
        self._close_after_download = False
        window = parent.window() if parent else None
        store = getattr(window, "store", None)
        self._frameless_mode = bool(getattr(store, "frameless_mode", False))
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle(f"搜索与选取: {self._game_name}")
        self.setMinimumSize(640, 540)
        self.resize(700, 640)
        self.setModal(True)
        self.setSizeGripEnabled(True)
        if self._frameless_mode:
            apply_dialog_frameless(self)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(14, 12, 14, 14)

        if self._frameless_mode:
            layout.addWidget(FramelessDialogTitleBar("素材导入", self))
        else:
            title = QLabel("素材导入")
            title.setObjectName("dialog-title")
            layout.addWidget(title)

        import webbrowser
        from urllib.parse import quote

        scroll = QScrollArea()
        scroll.setObjectName("resource-scroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        body = QWidget()
        body.setObjectName("resource-body")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(10, 10, 10, 10)
        body_layout.setSpacing(14)

        intro = QWidget()
        intro.setObjectName("resource-intro")
        intro_layout = QVBoxLayout(intro)
        intro_layout.setContentsMargins(18, 16, 18, 16)
        intro_layout.setSpacing(4)
        intro_title = QLabel(self._game_name)
        intro_title.setObjectName("resource-title")
        intro_hint = QLabel("从外部搜索获取封面或资料，回到这里粘贴链接和文本即可保存。")
        intro_hint.setObjectName("dialog-hint")
        intro_layout.addWidget(intro_title)
        intro_layout.addWidget(intro_hint)
        body_layout.addWidget(intro)

        # === 图片搜索 ===
        img_section = QFrame()
        img_section.setObjectName("resource-section")
        img_layout = QVBoxLayout(img_section)
        img_layout.setContentsMargins(18, 18, 18, 18)
        img_layout.setSpacing(12)

        img_header = QLabel("封面图片")
        img_header.setObjectName("resource-section-title")
        img_layout.addWidget(img_header)

        hint1 = QLabel("打开图片搜索后复制图片地址，再粘贴到下方输入框。")
        hint1.setObjectName("dialog-hint")
        img_layout.addWidget(hint1)

        img_row1 = QHBoxLayout()
        img_row1.setSpacing(10)

        for label, url in [
            ("百度图片", f"https://image.baidu.com/search/index?tn=baiduimage&word={quote(self._game_name + ' 游戏封面')}"),
            ("Bing 图片", f"https://www.bing.com/images/search?q={quote(self._game_name + ' game cover')}"),
            ("Google 图片", f"https://www.google.com/search?tbm=isch&q={quote(self._game_name + ' game cover')}"),
        ]:
            btn = QPushButton(label)
            btn.setObjectName("search-engine-btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, u=url: webbrowser.open(u))
            img_row1.addWidget(btn)

        img_layout.addLayout(img_row1)

        # 粘贴图片URL
        url_row = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("粘贴图片 URL (如 https://...)")
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

        img_layout.addLayout(url_row)

        # 图片预览
        self.cover_preview = QLabel()
        self.cover_preview.setFixedSize(160, 210)
        self.cover_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_preview.setObjectName("cover-preview-box")
        self.cover_preview.setText("图片预览区")
        self.cover_preview.hide()

        preview_row = QHBoxLayout()
        preview_row.addStretch()
        preview_row.addWidget(self.cover_preview)
        preview_row.addStretch()
        img_layout.addLayout(preview_row)

        # 下载状态
        self._status_label = QLabel("")
        self._status_label.setObjectName("dialog-status")
        img_layout.addWidget(self._status_label)
        body_layout.addWidget(img_section)

        # === 文本搜索 ===
        txt_section = QFrame()
        txt_section.setObjectName("resource-section")
        txt_layout = QVBoxLayout(txt_section)
        txt_layout.setContentsMargins(18, 18, 18, 18)
        txt_layout.setSpacing(12)

        txt_header = QLabel("介绍文本")
        txt_header.setObjectName("resource-section-title")
        txt_layout.addWidget(txt_header)

        hint2 = QLabel("打开资料来源后复制介绍文本，也可以直接手动整理。")
        hint2.setObjectName("dialog-hint")
        txt_layout.addWidget(hint2)

        txt_row1 = QHBoxLayout()
        txt_row1.setSpacing(10)

        for label, url in [
            ("百度", f"https://www.baidu.com/s?wd={quote(self._game_name + ' 游戏 介绍')}"),
            ("Bing", f"https://www.bing.com/search?q={quote(self._game_name + ' game intro')}"),
            ("Google", f"https://www.google.com/search?q={quote(self._game_name + ' game wiki')}"),
            ("维基百科", f"https://zh.wikipedia.org/wiki/Special:Search/{quote(self._game_name)}"),
        ]:
            btn = QPushButton(label)
            btn.setObjectName("search-engine-btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, u=url: webbrowser.open(u))
            txt_row1.addWidget(btn)

        txt_layout.addLayout(txt_row1)

        # 第二行：游戏特化搜索
        txt_row2 = QHBoxLayout()
        txt_row2.setSpacing(10)

        for label, url in [
            ("Steam", f"https://store.steampowered.com/search/?term={quote(self._game_name)}"),
            ("游民星空", f"https://so.gamersky.com/all?keyword={quote(self._game_name)}"),
            ("百度百科", f"https://baike.baidu.com/item/{quote(self._game_name)}"),
        ]:
            btn = QPushButton(label)
            btn.setObjectName("search-engine-btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, u=url: webbrowser.open(u))
            txt_row2.addWidget(btn)

        txt_row2.addStretch()
        txt_layout.addLayout(txt_row2)

        # 粘贴介绍文本
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("粘贴或输入游戏介绍...")
        self.desc_input.setMinimumHeight(130)
        txt_layout.addWidget(self.desc_input)

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

        txt_layout.addLayout(desc_row)
        body_layout.addWidget(txt_section)
        body_layout.addStretch()

        scroll.setWidget(body)
        layout.addWidget(scroll, 1)

        # 关闭
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
        if self._cached_pixmap and not self._cached_pixmap.isNull() and url == self._cached_url:
            self._open_crop_dialog(self._cached_pixmap)
        else:
            self._status_label.setText("正在下载封面...")
            self._download_and_show(url, preview_only=False)

    def _download_and_show(self, url: str, preview_only: bool = False):
        if self._downloader and self._downloader.isRunning():
            self._status_label.setText("已有图片正在加载，请稍候...")
            return
        self._close_after_download = False
        self._downloader = ImageDownloader(url)
        self._downloader.downloaded.connect(lambda ok, data, source_url=url: self._on_image_downloaded(ok, data, preview_only, source_url))
        self._downloader.finished.connect(self._on_downloader_finished)
        self._downloader.start()

    def _on_image_downloaded(self, ok: bool, data: bytes, preview_only: bool, source_url: str):
        if self._close_after_download:
            return
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
        self._cached_url = source_url

        if preview_only:
            self.cover_preview.setPixmap(fit_cover_pixmap(pixmap, 160, 210))
            self.cover_preview.show()
            self._status_label.setText("预览加载成功，点击「选为封面」裁剪并确认")
        else:
            # 下载完成后打开裁剪对话框
            self._open_crop_dialog(pixmap)

    def _on_downloader_finished(self):
        self._downloader = None
        if self._close_after_download:
            self._close_after_download = False
            QTimer.singleShot(0, self.close)

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
            self._close_after_download = True
            self._status_label.setText("图片下载中，完成后将自动关闭...")
            event.ignore()
            return
        super().closeEvent(event)
