import pyperclip
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFontMetrics, QFont
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGraphicsOpacityEffect, QToolTip

from db.database import toggle_favorite, delete_item


class ClipboardCard(QFrame):
    def __init__(self, item_id, category, is_fav, time_ago, content, parent):
        super().__init__()
        self.parent_window = parent
        self.item_id = item_id
        self.raw_content = content
        self.is_expanded = False
        self.is_fav = is_fav

        self.setObjectName("Card")

        # Main Layout: Luxurious padding and spacing
        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 25, 35, 25)
        layout.setSpacing(15)

        # --- HEADER ---
        header = QHBoxLayout()
        header.setSpacing(15)

        self.tag = QLabel(category.upper())
        self.tag.setObjectName(f"Tag{category.upper()}")

        self.time = QLabel(time_ago)
        self.time.setObjectName("TimeLabel")

        header.addWidget(self.tag)
        header.addWidget(self.time)
        header.addStretch()

        # Action Buttons: Sized for perfect circles (44x44)
        self.btn_fav = QPushButton("★")
        self.btn_fav.setToolTip("Mark as Favorite")

        self.btn_copy = QPushButton("❐")
        self.btn_copy.setToolTip("Copy to Clipboard")

        self.btn_del = QPushButton("✕")
        self.btn_del.setToolTip("Delete Snippet")
        self.btn_del.setObjectName("DeleteButton")  # Unique ID for red glow

        for b in [self.btn_fav, self.btn_copy]:
            b.setFixedSize(44, 44)
            b.setCursor(Qt.PointingHandCursor)
            b.setObjectName("ActionButton")
            header.addWidget(b)

        # Add Delete button separately to ensure ID is set correctly
        self.btn_del.setFixedSize(44, 44)
        self.btn_del.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.btn_del)

        if self.is_fav:
            self.btn_fav.setObjectName("FavActive")

        layout.addLayout(header)

        # --- CONTENT ---
        self.preview = QLabel()
        self.preview.setWordWrap(True)
        self.preview.setObjectName("PreviewText")
        self.preview.setCursor(Qt.PointingHandCursor)
        self.preview.mousePressEvent = self.toggle_expand

        layout.addWidget(self.preview)
        self.update_text()

        self.apply_styles()

        # Signals
        self.btn_copy.clicked.connect(self.copy)
        self.btn_fav.clicked.connect(self.toggle_fav)
        self.btn_del.clicked.connect(self.delete_item)

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
        self.btn_copy.setStyleSheet("color: #9ece6a; background: rgba(158, 206, 106, 0.15);")
        QTimer.singleShot(1000, lambda: (self.btn_copy.setText("❐"), self.btn_copy.setStyleSheet("")))

    def toggle_fav(self):
        self.is_fav = not self.is_fav
        toggle_favorite(self.item_id, int(self.is_fav))
        self.parent_window.refresh_items()

    def delete_item(self):
        delete_item(self.item_id)
        self.parent_window.refresh_items()

    def toggle_expand(self, e):
        self.is_expanded = not self.is_expanded
        self.update_text()

    def animate(self, delay):
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.setDuration(500)
        anim.setEasingCurve(QEasingCurve.OutExpo)
        QTimer.singleShot(delay, anim.start)

    def apply_styles(self):
        self.setStyleSheet("""
            #Card {
                background-color: #1a1b26;
                border: 1px solid #24283b;
                border-radius: 24px;
            }
            #Card:hover {
                border: 1px solid #414868;
                background-color: #1f2335;
            }
            #PreviewText {
                background-color: rgba(0, 0, 0, 0.3);
                border-radius: 16px;
                padding: 25px;
                color: #c0caf5;
                font-size: 16px;
                line-height: 1.6;
            }
            #TimeLabel { color: #565f89; font-size: 13px; font-weight: 600; }

            /* Default Round Hover Action Buttons (Blue) */
            #ActionButton, #DeleteButton {
                background: transparent;
                border: none;
                border-radius: 22px;
                color: #565f89;
                font-size: 20px;
            }

            #ActionButton:hover {
                background: rgba(122, 162, 247, 0.15);
                color: #7aa2f7;
            }

            /* Delete Button Specific Red Glow */
            #DeleteButton:hover {
                background: rgba(247, 118, 142, 0.15);
                color: #f7768e;
            }

            #FavActive {
                color: #e0af68 !important;
                background: rgba(224, 175, 104, 0.1) !important;
            }

            /* Chips */
            #TagTEXT, #TagCODE, #TagURL {
                font-size: 11px;
                font-weight: 800;
                border-radius: 8px;
                padding: 5px 12px;
                background: #16161e;
            }
            #TagTEXT { color: #9aa3ce; border: 1px solid #292e42; }
            #TagCODE { color: #bb9af7; border: 1px solid #bb9af7; }
            #TagURL { color: #7aa2f7; border: 1px solid #7aa2f7; }

            /* Modern Styled Tooltip */
            QToolTip {
                background-color: #1a1b26;
                color: #c0caf5;
                border: 1px solid #414868;
                padding: 5px 10px;
                border-radius: 6px;
                font-size: 12px;
            }
        """)