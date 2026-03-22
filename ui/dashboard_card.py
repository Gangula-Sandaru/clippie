import pyperclip
from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QGraphicsDropShadowEffect, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFontMetrics, QColor
from db.database import toggle_favorite, delete_item
from ui.dialog_window import ModernDialog


class ClipboardCard(QFrame):
    def __init__(self, item_id, category, is_fav, time_ago, content, parent, p, delay_ms=0):
        # Pass parent container to prevent PyQt from rendering this as a top-level OS window
        super().__init__(parent.container if hasattr(parent, 'container') else parent)
        self.parent_window = parent  # This MUST be the HistoryWindow/Dashboard
        self.item_id = item_id
        self.content = content
        self.is_fav = bool(is_fav)
        self.expanded = False
        self.p = p

        self.setObjectName("ItemCard")
        self.setCursor(Qt.PointingHandCursor)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(22, 18, 22, 18)
        self.main_layout.setSpacing(8)

        # --- Header ---
        header = QHBoxLayout()
        self.category = str(category).upper() if category else "TEXT"
        self.tag = QLabel(self.category)
        self.tag.setObjectName(f"Tag{self.category}")
        self.time_lbl = QLabel(time_ago)
        self.time_lbl.setObjectName("TimeLabel")
        header.addWidget(self.tag)
        header.addWidget(self.time_lbl)
        header.addStretch()

        # --- Round Action Buttons ---
        self.btn_fav = self._create_action_btn("★", "FavBtn", "#FFD700")
        self.btn_edit = self._create_action_btn("✏", "EditBtn", p['accent'])
        self.btn_copy = self._create_action_btn("❐", "CopyBtn", p['accent'])
        self.btn_delete = self._create_action_btn("🗑", "DelBtn", "#FF4B4B")

        self.btn_fav.clicked.connect(self.toggle_fav)
        self.btn_edit.clicked.connect(self.edit_me)
        self.btn_copy.clicked.connect(self.copy_me)
        self.btn_delete.clicked.connect(self.delete_me)

        header.addWidget(self.btn_fav)
        header.addWidget(self.btn_edit)
        header.addWidget(self.btn_copy)
        header.addWidget(self.btn_delete)
        self.main_layout.addLayout(header)

        self.content_lbl = QLabel()
        self.content_lbl.setObjectName("ContentLabel")
        self.content_lbl.setWordWrap(True)
        self.main_layout.addWidget(self.content_lbl)

        self.hint = QLabel("Show More ↓")
        self.hint.setObjectName("TimeLabel")
        self.main_layout.addWidget(self.hint)

        self.update_content()
        self.apply_styles(p)

        # --- APPEARANCE ANIMATION ---
        # We use a staggered show() instead of opacity to prevent nested QGraphicsEffect crashes
        # since the child buttons already use QGraphicsDropShadowEffect.
        self.hide()
        if delay_ms > 0:
            QTimer.singleShot(delay_ms, self.show)
        else:
            QTimer.singleShot(5, self.show)

    def _create_action_btn(self, icon, obj_name, glow_color):
        btn = QPushButton(icon)
        btn.setFixedSize(38, 38)
        btn.setObjectName(obj_name)
        glow = QGraphicsDropShadowEffect(btn)
        glow.setBlurRadius(0)
        glow.setOffset(0, 0)
        glow.setColor(QColor(glow_color))
        btn.setGraphicsEffect(glow)
        btn.enterEvent = lambda e: glow.setBlurRadius(20)
        btn.leaveEvent = lambda e: glow.setBlurRadius(0)
        return btn

    def apply_styles(self, p):
        btn_bg = p['main_bg']
        fav_color = "#FFD700" if self.is_fav else "transparent"
        fav_bg_state = btn_bg if self.is_fav else "transparent"
        fav_border = p['card_border'] if self.is_fav else "transparent"

        self.setStyleSheet(f"""
            #ItemCard {{ background-color: {p['widget_bg']}; border-radius: 20px; border: 1px solid {p['card_border']}; margin: 4px 10px; }}
            #ItemCard:hover {{ background-color: {p['card_hover_bg']}; border: 1px solid {p['accent']}; }}
            #FavBtn, #EditBtn, #CopyBtn, #DelBtn {{ background-color: transparent; border: 1px solid transparent; border-radius: 19px; color: transparent; font-size: 18px; }}
            #ItemCard:hover #EditBtn, #ItemCard:hover #CopyBtn, #ItemCard:hover #DelBtn {{ background-color: {btn_bg}; color: {p['text_dim']}; border: 1px solid {p['card_border']}; }}
            #FavBtn {{ background-color: {fav_bg_state} !important; color: {fav_color} !important; border: 1px solid {fav_border} !important; }}
            #ItemCard:hover #FavBtn {{ background-color: {btn_bg}; color: {"#FFD700" if self.is_fav else p['text_dim']}; border: 1px solid {p['card_border']}; }}
            #FavBtn:hover {{ color: #FFD700 !important; border: 1px solid #FFD700 !important; }}
            #DelBtn:hover {{ color: #FF4B4B !important; border: 1px solid #FF4B4B !important; }}
            #CopyBtn:hover {{ color: {p['accent']} !important; border: 1px solid {p['accent']} !important; }}
            #EditBtn:hover {{ color: {p['accent']} !important; border: 1px solid {p['accent']} !important; }}
            QLabel#ContentLabel {{ color: {p['text_main']}; font-size: 15px; padding: 5px 0px; }}
            QLabel#TimeLabel {{ color: {p['text_dim']}; font-size: 12px; }}
            [objectName^="Tag"] {{ font-size: 10px; font-weight: 900; border-radius: 8px; padding: 2px 10px; background-color: {p['main_bg']}; color: {p['accent']}; border: 1px solid {p['card_border']}; }}
        """)

    def toggle_fav(self):
        toggle_favorite(self.item_id, not self.is_fav)
        # Call the refresh method on parent window
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
        # Create the modern dialog
        dialog = ModernDialog(
            "Confirm Action",
            "This item will be permanently removed from your history.",
            self.p,
            self.parent_window
        )

        # Center over the HistoryWindow
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
            import hashlib
            from PIL import Image
            
            try:
                pil_img = Image.open(self.content)
                if pil_img.mode != 'RGB': pil_img = pil_img.convert('RGB')
                monitor.last_ui_image_hash = hashlib.md5(pil_img.tobytes()).hexdigest()
            except Exception: pass
            
            cb = QApplication.clipboard()
            cb.setImage(QImage(self.content), QClipboard.Clipboard)
        else:
            pyperclip.copy(self.content)
            
        self.btn_copy.setText("✓")
        QTimer.singleShot(1000, lambda: self.btn_copy.setText("❐"))

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
        if self.expanded:
            self.content_lbl.setText(self.content)
            self.hint.setText("Show Less ↑")
        else:
            clean = self.content.replace("\n", " ")
            elided = metrics.elidedText(clean, Qt.ElideRight, 400)
            self.content_lbl.setText(elided)
            self.hint.setText("Show More ↓")

    def mousePressEvent(self, event):
        if self.childAt(event.pos()) in [self.btn_fav, self.btn_edit, self.btn_copy, self.btn_delete]:
            return
        self.expanded = not self.expanded
        self.update_content()
        # Ensure the container resizes to fit the expanded text
        QTimer.singleShot(10, lambda: self.parent_window.container.adjustSize())

