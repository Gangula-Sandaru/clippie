import pyperclip
from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QGraphicsDropShadowEffect, QMessageBox, QTextEdit)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFontMetrics, QColor
from db.database import toggle_favorite, delete_item
from ui.dialog_window import ModernDialog


class ClipboardCard(QFrame):
    def __init__(self, item_id, category, is_fav, time_ago, content, parent, p, delay_ms=0, html=None):
        super().__init__(parent.container if hasattr(parent, 'container') else parent)
        self.parent_window = parent
        self.item_id = item_id
        self.content = content
        self.is_fav = bool(is_fav)
        self.expanded = False
        self.show_html_preview = False
        self.p = p
        self.category = str(category).upper() if category else "TEXT"
        self.is_html_content = "<html>" in self.content.lower() or "<!doctype html>" in self.content.lower() or self.category == "HTML"
        self.html_content = html if html else (content if self.is_html_content else None)

        self.setObjectName("ItemCard")
        self.setCursor(Qt.PointingHandCursor)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(22, 20, 22, 20)
        self.main_layout.setSpacing(14)

        header = QHBoxLayout()
        self.tag = QLabel(self.category)
        self.tag.setObjectName(f"Tag{self.category}")
        self.time_lbl = QLabel(time_ago)
        self.time_lbl.setObjectName("TimeLabel")
        header.addWidget(self.tag)
        header.addWidget(self.time_lbl)
        header.addStretch()

        self.btn_fav = self._create_action_btn("★", "FavBtn", "#FFD700")
        self.btn_edit = self._create_action_btn("✎", "EditBtn", p['accent'])
        self.btn_copy = self._create_action_btn("❐", "CopyBtn", p['accent'])
        self.btn_delete = self._create_action_btn("🗑", "DelBtn", "#FF4B4B")

        self.btn_fav.clicked.connect(self.toggle_fav)
        self.btn_edit.clicked.connect(self.edit_me)
        self.btn_copy.clicked.connect(self.copy_me)
        self.btn_delete.clicked.connect(self.delete_me)

        if self.is_html_content:
            self.btn_toggle_html = self._create_action_btn("SHOW PREVIEW", "HtmlBtn", p['accent'])
            self.btn_toggle_html.setFixedSize(110, 38)
            self.btn_toggle_html.setToolTip("Toggle Code/Preview View")
            self.btn_toggle_html.clicked.connect(self.toggle_html_mode)
            header.addWidget(self.btn_toggle_html)

        header.addWidget(self.btn_fav)
        header.addWidget(self.btn_edit)
        header.addWidget(self.btn_copy)
        header.addWidget(self.btn_delete)
        self.main_layout.addLayout(header)

        self.content_lbl = QLabel()
        self.content_lbl.setObjectName("ContentLabel")
        self.content_lbl.setWordWrap(True)
        self.main_layout.addWidget(self.content_lbl)

        # Scrollable area for expanded code/text
        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        self.content_text.setObjectName("ContentArea")
        self.content_text.setMaximumHeight(400)
        self.content_text.setFrameStyle(0) # No border
        self.content_text.hide()
        self.main_layout.addWidget(self.content_text)

        self.hint = QLabel("Show More ↓")
        self.hint.setObjectName("HintLabel")
        self.main_layout.addWidget(self.hint)

        self.update_content()
        self.apply_palette(p)
        self.apply_styles(p)

        self.hide()
        if delay_ms > 0:
            QTimer.singleShot(delay_ms, self.show)
        else:
            QTimer.singleShot(5, self.show)

    def _create_action_btn(self, icon, obj_name, glow_color):
        btn = QPushButton(icon)
        btn.setFixedSize(38, 38)
        btn.setObjectName(obj_name)
        btn.setCursor(Qt.PointingHandCursor)
        
        glow = QGraphicsDropShadowEffect(btn)
        glow.setBlurRadius(0)
        glow.setOffset(0, 0)
        glow.setColor(QColor(glow_color))
        btn.setGraphicsEffect(glow)
        
        # Enhanced glow triggers
        is_del = obj_name == "DelBtn"
        btn.enterEvent = lambda e: glow.setBlurRadius(30 if is_del else 20)
        btn.leaveEvent = lambda e: glow.setBlurRadius(0)
        return btn

    def apply_palette(self, p):
        from PyQt5.QtGui import QPalette
        pal = self.palette()
        txt_color = QColor(p['text_main'])
        dim_color = QColor(p['text_dim'])
        pal.setColor(QPalette.WindowText, txt_color)
        pal.setColor(QPalette.Text, txt_color)
        pal.setColor(QPalette.ButtonText, txt_color)
        pal.setColor(QPalette.PlaceholderText, dim_color)
        self.setPalette(pal)
        self.content_lbl.setPalette(pal)
        self.content_text.setPalette(pal)

    def apply_styles(self, p):
        btn_bg = p['main_bg']
        fav_color = "#FFD700" if self.is_fav else "transparent"
        fav_bg_state = btn_bg if self.is_fav else "transparent"
        fav_border = p['card_border'] if self.is_fav else "transparent"

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
            
            #FavBtn, #EditBtn, #CopyBtn {{ 
                background-color: transparent; 
                border: 1px solid transparent; 
                border-radius: 10px; 
                color: {p['text_dim']}44; 
                font-family: 'Segoe UI', 'Segoe UI Symbol', sans-serif;
                font-size: 18px; 
                font-weight: normal;
                outline: none;
            }}

            #DelBtn {{ 
                background-color: transparent; 
                border: 1px solid transparent; 
                border-radius: 10px; 
                color: {p['text_dim']}44; 
                font-family: 'Segoe UI Symbol', 'Segoe UI', sans-serif;
                font-size: 19px; 
                font-weight: 300;
                outline: none;
            }}
            
            #HtmlBtn, #HintLabel, #TimeLabel {{ 
                background-color: transparent; 
                border: none; 
                color: {p['text_dim']}; 
                font-family: 'Segoe UI', 'Tahoma', sans-serif;
                font-size: 12px; 
                font-weight: 400;
                outline: none;
            }}
            
            #ItemCard:hover #EditBtn, #ItemCard:hover #CopyBtn, #ItemCard:hover #DelBtn {{ 
                background-color: {btn_bg}; 
                color: {p['text_dim']}; 
                border: 1px solid {p['card_border']}; 
            }}
            
            #ItemCard:hover #HtmlBtn {{ 
                color: {p['accent']}; 
            }}
            
            #FavBtn {{ 
                background-color: {fav_bg_state} !important; 
                color: {fav_color} !important; 
                border: 1px solid {fav_border} !important; 
            }}
            
            #ItemCard:hover #FavBtn {{ 
                background-color: {btn_bg}; 
                color: {"#FFD700" if self.is_fav else p['text_dim']}; 
                border: 1px solid {p['card_border']}; 
            }}
            
            #FavBtn:hover {{ color: #FFD700 !important; border: 1px solid #FFD700 !important; }}
            #DelBtn:hover {{ color: #FF6B6B !important; border: 1px solid #FF6B6B !important; }}
            #CopyBtn:hover {{ color: {p['accent']} !important; border: 1px solid {p['accent']} !important; }}
            #EditBtn:hover {{ color: {p['accent']} !important; border: 1px solid {p['accent']} !important; }}
            #HtmlBtn:hover {{ color: {p['accent']} !important; text-decoration: underline; }}
            
            QLabel#ContentLabel {{ 
                color: {p['text_main']} !important; 
                font-family: 'Segoe UI', 'Tahoma', sans-serif;
                font-size: 15px; 
                font-weight: 400; 
                padding: 10px 0px; 
            }}
            
            QTextEdit#ContentArea {{ 
                background: transparent; 
                color: {p['text_main']} !important; 
                font-family: 'Segoe UI', 'Tahoma', sans-serif;
                font-size: 15px; 
                font-weight: 400;
                border: none; 
                padding: 10px 0px; 
            }}
            
            QTextEdit#ContentArea QScrollBar:vertical {{
                background: transparent;
                width: 4px;
            }}
            QTextEdit#ContentArea QScrollBar::handle:vertical {{
                background: {p['card_border']};
                border-radius: 2px;
            }}
            
            #HtmlBtn:hover, #HintLabel:hover {{ color: {p['accent']} !important; text-decoration: underline; }}
            
            [objectName^="Tag"] {{ 
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

    def toggle_fav(self):
        toggle_favorite(self.item_id, not self.is_fav)
        if hasattr(self.parent_window, "refresh_items"):
            self.parent_window.refresh_items()

    def edit_me(self):
        if getattr(self, 'category', '') == "IMAGE":
            return
            
        from ui.dialog_window import EditDialog
        dialog = EditDialog(self.content, self.p, self.parent_window)
        parent_geo = self.parent_window.geometry()
        dialog.move(
            parent_geo.center().x() - dialog.width() // 2,
            parent_geo.center().y() - dialog.height() // 2
        )

        if dialog.exec_():
            new_text = dialog.updated_content
            if new_text != self.content:
                from db.database import update_item
                update_item(self.item_id, new_text)
                if hasattr(self.parent_window, "refresh_items"):
                    self.parent_window.refresh_items()

    def delete_me(self):
        dialog = ModernDialog(
            "Confirm Action",
            "This item will be permanently removed from your history.",
            self.p,
            self.parent_window
        )

        parent_geo = self.parent_window.geometry()
        dialog.move(
            parent_geo.center().x() - dialog.width() // 2,
            parent_geo.center().y() - dialog.height() // 2
        )

        if dialog.exec_():
            if dialog.result_status:
                delete_item(self.item_id)
                if hasattr(self.parent_window, "refresh_items"):
                    self.parent_window.refresh_items()

    def copy_me(self):
        from clipboard import monitor
        if getattr(self, 'category', '') == "IMAGE":
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtGui import QImage, QClipboard
            from PyQt5.QtCore import QUrl, QMimeData, QCoreApplication
            import hashlib
            from PIL import Image
            
            try:
                pil_img = Image.open(self.content)
                if pil_img.mode != 'RGB': pil_img = pil_img.convert('RGB')
                monitor.last_ui_image_hash = hashlib.md5(pil_img.tobytes()).hexdigest()
            except Exception: pass
            
            cb = QApplication.clipboard()
            self._temp_mime = QMimeData()
            self._temp_mime.setImageData(QImage(self.content))
            self._temp_mime.setUrls([QUrl.fromLocalFile(self.content)])
            cb.setMimeData(self._temp_mime)
            QCoreApplication.processEvents()
        else:
            pyperclip.copy(self.content)
            
        self.btn_copy.setText("✓")
        QTimer.singleShot(1000, lambda: self.btn_copy.setText("❐"))

    def toggle_html_mode(self):
        self.show_html_preview = not self.show_html_preview
        if self.show_html_preview:
            # We are now in PREVIEW mode, button shows text to go back to CODE
            self.expanded = True
            self.btn_toggle_html.setText("SHOW CODE")
        else:
            # We are now in CODE mode, button shows text to go to PREVIEW
            self.btn_toggle_html.setText("SHOW PREVIEW")
        self.update_content()
        self.apply_styles(self.p)
        # Refresh layout height
        QTimer.singleShot(10, lambda: self.parent_window.container.adjustSize())

    def update_content(self):
        if getattr(self, 'category', '') == "IMAGE":
            from PyQt5.QtGui import QPixmap
            pixmap = QPixmap(self.content)
            if not pixmap.isNull():
                if self.expanded:
                    self.content_lbl.setPixmap(pixmap.scaledToWidth(400, Qt.SmoothTransformation))
                    self.hint.setText("Show Less ↑")
                else:
                    self.content_lbl.setPixmap(pixmap.scaled(200, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    self.hint.setText("Show More ↓")
            else:
                self.content_lbl.setText("Image not found")
            return

        metrics = QFontMetrics(self.content_lbl.font())
        if self.is_html_content and self.show_html_preview:
            if self.expanded:
                self.content_lbl.hide()
                self.content_text.show()
                # Use setHtml for preview with theme injection and non-bold fonts
                themed_html = f"<div style='color: {self.p['text_main']}; font-family: Segoe UI, sans-serif; font-weight: 400; font-size: 15px;'>{self.content}</div>"
                self.content_text.setHtml(themed_html)
                self.hint.setText("Show Less ↑")
            else:
                self.content_text.hide()
                self.content_lbl.show()
                self.content_lbl.setTextFormat(Qt.PlainText)
                clean = self.content.replace("\n", " ")
                elided = metrics.elidedText(clean, Qt.ElideRight, 400)
                self.content_lbl.setText(elided)
                self.hint.setText("Show More ↓")
        elif self.expanded:
            self.content_lbl.hide()
            self.content_text.show()
            # Use setPlainText for raw code/text
            self.content_text.setPlainText(self.content)
            self.hint.setText("Show Less ↑")
        else:
            self.content_text.hide()
            self.content_lbl.show()
            self.content_lbl.setTextFormat(Qt.PlainText)
            clean = self.content.replace("\n", " ")
            elided = metrics.elidedText(clean, Qt.ElideRight, 400)
            self.content_lbl.setText(elided)
            self.hint.setText("Show More ↓")

    def mousePressEvent(self, event):
        if self.childAt(event.pos()) in [self.btn_fav, self.btn_edit, self.btn_copy, self.btn_delete]:
            return
        self.expanded = not self.expanded
        self.update_content()
        QTimer.singleShot(10, lambda: self.parent_window.container.adjustSize())

        QTimer.singleShot(10, lambda: self.parent_window.container.adjustSize())

