import pyperclip
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFontMetrics, QFont
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGraphicsOpacityEffect
from db.database import toggle_favorite, delete_item

class ClipboardCard(QFrame):
    def __init__(self, item_id, category, is_fav, time_ago, content, parent, p):
        super().__init__()
        self.parent_window = parent
        self.item_id = item_id
        self.raw_content = content
        self.is_expanded = False
        self.is_fav = is_fav

        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 25, 35, 25)
        layout.setSpacing(15)

        # Header
        header = QHBoxLayout()
        self.tag = QLabel(category.upper())
        self.tag.setObjectName(f"Tag{category.upper()}")
        self.time = QLabel(time_ago)
        self.time.setObjectName("TimeLabel")
        header.addWidget(self.tag)
        header.addWidget(self.time)
        header.addStretch()

        self.btn_fav = QPushButton("★")
        self.btn_copy = QPushButton("❐")
        self.btn_del = QPushButton("✕")
        self.btn_del.setObjectName("DeleteButton")

        for b in [self.btn_fav, self.btn_copy, self.btn_del]:
            b.setFixedSize(44, 44)
            b.setCursor(Qt.PointingHandCursor)
            if b != self.btn_del: b.setObjectName("ActionButton")
            header.addWidget(b)

        if self.is_fav: self.btn_fav.setObjectName("FavActive")
        layout.addLayout(header)

        self.preview = QLabel()
        self.preview.setWordWrap(True)
        self.preview.setObjectName("PreviewText")
        layout.addWidget(self.preview)

        self.update_text()
        self.apply_styles(p) # Use the palette passed from parent

        self.btn_copy.clicked.connect(self.copy)
        self.btn_fav.clicked.connect(self.toggle_fav)
        self.btn_del.clicked.connect(self.delete_item)

    def apply_styles(self, p):
        self.setStyleSheet(f"""
            #Card {{ background-color: {p['card_bg']}; border: 1px solid {p['card_border']}; border-radius: 24px; }}
            #Card:hover {{ border: 1px solid {p['card_hover_border']}; background-color: {p['card_hover_bg']}; }}
            #PreviewText {{ background-color: {p['main_bg']}; border-radius: 16px; padding: 25px; color: {p['text_main']}; font-size: 16px; }}
            #TimeLabel {{ color: {p['text_dim']}; font-size: 13px; font-weight: 600; }}
            #ActionButton, #DeleteButton {{ background: transparent; color: {p['text_dim']}; font-size: 20px; border-radius: 22px; }}
            #ActionButton:hover {{ background: {p['danger_hover']}; color: {p['accent']}; }}
            #DeleteButton:hover {{ background: {p['danger_hover']}; color: {p['danger_text']}; }}
            #FavActive {{ color: #e0af68 !important; background: rgba(224, 175, 104, 0.1) !important; }}
            #TagTEXT, #TagCODE, #TagURL {{ font-size: 11px; font-weight: 800; border-radius: 8px; padding: 5px 12px; background: {p['widget_bg']}; color: {p['accent']}; border: 1px solid {p['card_border']}; }}
        """)

    def update_text(self):
        font = QFont("Segoe UI", 12)
        if self.is_expanded:
            self.preview.setText(self.raw_content)
        else:
            metrics = QFontMetrics(font)
            text = metrics.elidedText(self.raw_content.replace("\n", " "), Qt.ElideRight, 850)
            self.preview.setText(text)

    def copy(self):
        pyperclip.copy(self.raw_content)
        self.btn_copy.setText("✓")
        QTimer.singleShot(1000, lambda: self.btn_copy.setText("❐"))

    def toggle_fav(self):
        self.is_fav = not self.is_fav
        toggle_favorite(self.item_id, int(self.is_fav))
        self.parent_window.refresh_items()

    def delete_item(self):
        delete_item(self.item_id)
        self.parent_window.refresh_items()

    def animate(self, delay):
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setStartValue(0); anim.setEndValue(1); anim.setDuration(400)
        QTimer.singleShot(delay, anim.start)