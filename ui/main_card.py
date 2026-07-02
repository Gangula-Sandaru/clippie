import pyperclip
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFontMetrics


class ClipboardItemWidget(QFrame):
    def __init__(self, content, category="TEXT", time_ago="Just now", p=None):
        super().__init__()
        self.setObjectName("ItemCard")

        self.setFocusPolicy(Qt.NoFocus)
        self.setAttribute(Qt.WA_Hover)

        self.raw_content = content
        self.category = category.upper() if category else "TEXT"
        self.palette = p

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        header = QHBoxLayout()
        header.setAlignment(Qt.AlignVCenter)

        self.tag_label = QLabel(self.category)
        self.tag_label.setObjectName(f"Tag{self.category}")
        self.tag_label.setFixedHeight(24)

        self.time_label = QLabel(time_ago)
        self.time_label.setObjectName("TimeLabel")

        self.actions_container = QWidget()
        self.actions_container.setFixedWidth(35)
        actions_layout = QHBoxLayout(self.actions_container)
        actions_layout.setContentsMargins(0, 0, 0, 0)

        self.copy_btn = QPushButton("❐")
        self.copy_btn.setFixedSize(32, 32)
        self.copy_btn.setCursor(Qt.PointingHandCursor)
        self.copy_btn.setObjectName("ActionBtn")
        self.copy_btn.setFocusPolicy(Qt.NoFocus)
        self.copy_btn.clicked.connect(self.copy_to_clipboard)

        actions_layout.addWidget(self.copy_btn)

        header.addWidget(self.tag_label)
        header.addSpacing(12)
        header.addWidget(self.time_label)
        header.addStretch()
        header.addWidget(self.actions_container)

        self.content_label = QLabel()
        self.content_label.setObjectName("ContentLabel")

        if self.category == "IMAGE":
            from PyQt5.QtGui import QPixmap
            pixmap = QPixmap(self.raw_content)
            if not pixmap.isNull():
                self.content_label.setPixmap(pixmap.scaled(300, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                self.content_label.setText("Image not found")

        layout.addLayout(header)
        layout.addWidget(self.content_label)

        if p: self.apply_styles(p)
        if self.category != "IMAGE":
            QTimer.singleShot(10, self.update_elided_text)

    def _reset_btn(self):
        try:
            self.copy_btn.setText("❐")
        except RuntimeError:
            pass

    def copy_to_clipboard(self):
        from clipboard import monitor
        if self.category == "IMAGE":
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtGui import QImage, QClipboard
            from PyQt5.QtCore import QUrl, QMimeData, QCoreApplication
            import hashlib
            from PIL import Image

            try:
                pil_img = Image.open(self.raw_content)
                if pil_img.mode != 'RGB': pil_img = pil_img.convert('RGB')
                monitor.last_ui_image_hash = hashlib.md5(pil_img.tobytes()).hexdigest()
            except Exception: pass
            
            cb = QApplication.clipboard()
            self._temp_mime = QMimeData()
            self._temp_mime.setImageData(QImage(self.raw_content))
            self._temp_mime.setUrls([QUrl.fromLocalFile(self.raw_content)])
            cb.setMimeData(self._temp_mime)
            QCoreApplication.processEvents()
        else:
            monitor.last_ui_copy = self.raw_content
            pyperclip.copy(self.raw_content)

        self.copy_btn.setText("✓")
        QTimer.singleShot(800, self._reset_btn)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            from clipboard import monitor
            if self.category == "IMAGE":
                from PyQt5.QtWidgets import QApplication
                from PyQt5.QtGui import QImage, QClipboard
                from PyQt5.QtCore import QUrl, QMimeData, QCoreApplication
                import hashlib
                from PIL import Image

                try:
                    pil_img = Image.open(self.raw_content)
                    if pil_img.mode != 'RGB': pil_img = pil_img.convert('RGB')
                    monitor.last_ui_image_hash = hashlib.md5(pil_img.tobytes()).hexdigest()
                except Exception: pass

                cb = QApplication.clipboard()
                self._temp_mime = QMimeData()
                self._temp_mime.setImageData(QImage(self.raw_content))
                self._temp_mime.setUrls([QUrl.fromLocalFile(self.raw_content)])
                cb.setMimeData(self._temp_mime)
                QCoreApplication.processEvents()
            else:
                monitor.last_ui_copy = self.raw_content
                pyperclip.copy(self.raw_content)

            self.copy_btn.setText("✓")
            old_time = self.time_label.text()
            self.time_label.setText("Pasted!")
            if self.palette:
                self.time_label.setStyleSheet(f"color: {self.palette['accent']}; font-weight: bold;")
            else:
                self.time_label.setStyleSheet("color: #4ade80; font-weight: bold;")

            def reset():
                self._reset_btn()
                try:
                    self.time_label.setText(old_time)
                    if self.palette:
                        self.time_label.setStyleSheet(f"color: {self.palette['text_dim']}; font-weight: normal;")
                except RuntimeError:
                    pass

            QTimer.singleShot(2000, reset)

            import keyboard
            delay = 250 if self.category == "IMAGE" else 50
            QTimer.singleShot(delay, lambda: keyboard.send('ctrl+v'))

        super().mouseReleaseEvent(event)

    def apply_styles(self, p):
        self.setStyleSheet(f"""
            #ItemCard {{ 
                background-color: {p['widget_bg']}; 
                border-radius: 20px; 
                border: 1px solid {p['card_border']}; 
                margin: 3px 10px; 
                outline: none;
            }}
            #ItemCard:hover {{ 
                background-color: {p['card_hover_bg']}; 
                border: 2px solid {p['accent']}; 
            }}
            #ActionBtn {{ 
                background-color: transparent; 
                color: transparent;
                border: none; 
                border-radius: 10px; 
                font-size: 18px;
                outline: none;
            }}
            #ItemCard:hover #ActionBtn {{
                background-color: {p['main_bg']}; 
                color: {p['text_dim']};
                border: 1px solid {p['card_border']}; 
            }}
            #ActionBtn:hover {{
                color: {p['accent']} !important;
                border: 1px solid {p['accent']} !important;
            }}
            QLabel#ContentLabel {{ 
                color: {p['text_main']}; 
                font-family: 'Segoe UI Variable Text', 'Segoe UI', sans-serif;
                font-size: 15px; 
                font-weight: 400; 
                padding: 10px 0px; 
                letter-spacing: -0.1px;
            }}
            QLabel#TimeLabel {{ 
                color: {p['text_dim']}; 
                font-family: 'Segoe UI Variable Text', 'Segoe UI', sans-serif;
                font-size: 12px; 
                letter-spacing: -0.1px;
            }}
            [objectName^="Tag"] {{ 
                font-family: 'Segoe UI Variable Text', 'Segoe UI', sans-serif;
                font-size: 10px; 
                font-weight: 800; 
                letter-spacing: 0.5px;
                border-radius: 8px; 
                padding: 0 10px;
                background-color: {p['main_bg']}; 
                color: {p['text_dim']};
                border: 1px solid {p['card_border']};
                text-transform: uppercase;
            }}
        """)

    def update_elided_text(self):
        if self.category == "IMAGE": return
        metrics = QFontMetrics(self.content_label.font())
        display_text = self.raw_content.replace('\n', ' ').strip()
        target_width = self.width() - 95
        if target_width > 0:
            self.content_label.setText(metrics.elidedText(display_text, Qt.ElideRight, target_width))

    def resizeEvent(self, event):
        self.update_elided_text()
        super().resizeEvent(event)
