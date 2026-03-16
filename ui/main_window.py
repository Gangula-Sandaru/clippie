from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QHBoxLayout, QFrame, \
    QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFontMetrics
from db.database import get_recent_items, get_time_ago
import pyperclip


class ClipboardItemWidget(QFrame):
    def __init__(self, content, category="Text", time_ago="Just now"):
        super().__init__()
        self.setObjectName("ItemCard")
        self.raw_content = content

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(6)

        header_layout = QHBoxLayout()

        # 1. Tag
        self.tag_label = QLabel(category.upper())
        self.tag_label.setObjectName(f"Tag{category}")

        # 2. Time
        self.time_label = QLabel(time_ago)
        self.time_label.setObjectName("TimeLabel")

        # 3. Copy Icon (The 'Double Box' ❐)
        self.copy_icon = QLabel("❐")
        self.copy_icon.setObjectName("CopyIcon")
        self.copy_icon.setFixedWidth(20)
        self.copy_icon.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # --- OPACITY FIX ---
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0.0)  # Hidden by default
        self.copy_icon.setGraphicsEffect(self.opacity_effect)

        header_layout.addWidget(self.tag_label)
        header_layout.addSpacing(10)
        header_layout.addWidget(self.time_label)
        header_layout.addStretch()
        header_layout.addWidget(self.copy_icon)

        # 4. Content (Single line)
        self.content_label = QLabel()
        self.content_label.setObjectName("ContentLabel")

        layout.addLayout(header_layout)
        layout.addWidget(self.content_label)

    def enterEvent(self, event):
        self.opacity_effect.setOpacity(1.0)  # Show on hover
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.opacity_effect.setOpacity(0.0)  # Hide on leave
        super().leaveEvent(event)

    def paintEvent(self, event):
        metrics = QFontMetrics(self.content_label.font())
        display_text = self.raw_content.replace('\n', ' ').strip()
        elided = metrics.elidedText(display_text, Qt.ElideRight, self.width() - 50)
        self.content_label.setText(elided)
        super().paintEvent(event)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(360, 520)

        self.container = QFrame(self)
        self.container.setObjectName("Container")
        self.container.setFixedSize(360, 520)

        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(20, 20, 20, 15)

        header = QLabel("🕒 Recent Copies")
        header.setObjectName("MainHeader")
        self.main_layout.addWidget(header)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("HistoryList")
        self.list_widget.setSpacing(8)
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_widget.itemClicked.connect(self.copy_selection)
        self.main_layout.addWidget(self.list_widget)

        self.footer = QLabel("View All →")
        self.footer.setAlignment(Qt.AlignCenter)
        self.footer.setObjectName("FooterLink")
        self.main_layout.addWidget(self.footer)

        self.apply_styles()
        self.load_items()

    def load_items(self):
        self.list_widget.clear()
        items = get_recent_items()
        for item in items:
            cw = ClipboardItemWidget(item[1], item[2], get_time_ago(item[4]))
            li = QListWidgetItem(self.list_widget)
            li.setSizeHint(cw.sizeHint())
            self.list_widget.addItem(li)
            self.list_widget.setItemWidget(li, cw)

    def copy_selection(self, item):
        widget = self.list_widget.itemWidget(item)
        pyperclip.copy(widget.raw_content)
        h = self.findChild(QLabel, "MainHeader")
        h.setText("✅ Copied!")
        h.setStyleSheet("color: #7aa2f7;")
        QTimer.singleShot(1000, lambda: (h.setText("🕒 Recent Copies"), h.setStyleSheet("color: white;")))

    def apply_styles(self):
        self.setStyleSheet("""
            #Container { background-color: #0b0e14; border-radius: 18px; border: 1px solid #1a1f26; }
            #MainHeader { color: #ffffff; font-size: 15px; font-weight: 700; padding: 5px; }
            #HistoryList { background: transparent; border: none; outline: none; }
            #ItemCard { background-color: #141923; border-radius: 12px; border: 1px solid #1f2631; }
            #ItemCard:hover { background-color: #1c2331; border: 1px solid #2d384d; }
            #CopyIcon { color: #7aa2f7; font-size: 14px; font-weight: bold; }
            #ContentLabel { color: #ffffff; font-size: 13px; font-weight: 600; }
            #TimeLabel { color: #565f89; font-size: 11px; }
            #TagCode { background-color: #311b47; color: #bb9af7; border-radius: 4px; padding: 2px 8px; font-size: 10px; font-weight: bold; }
            #TagURL { background-color: #1a273e; color: #7aa2f7; border-radius: 4px; padding: 2px 8px; font-size: 10px; font-weight: bold; }
            #TagText { background-color: #222a39; color: #99a3ba; border-radius: 4px; padding: 2px 8px; font-size: 10px; font-weight: bold; }
            #FooterLink { color: #3d59a1; font-size: 13px; font-weight: 600; padding: 10px; border-top: 1px solid #1a1f26; }
            QScrollBar:vertical { border: none; background: transparent; width: 4px; }
            QScrollBar::handle:vertical { background: #2d384d; border-radius: 2px; }
        """)