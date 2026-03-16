from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QHBoxLayout, QFrame
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFontMetrics, QColor
from db.database import get_recent_items, get_time_ago  # Ensure get_time_ago is in your db file
import pyperclip


class ClipboardItemWidget(QFrame):
    def __init__(self, content, category="Text", time_ago="Just now", is_favorite=0):
        super().__init__()
        self.setObjectName("ItemCard")
        self.raw_content = content

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(4)

        # Header: Tag, Favorite Star, and Time
        header_layout = QHBoxLayout()

        self.tag_label = QLabel(category.upper())
        self.tag_label.setObjectName(f"Tag{category}")

        # Show a star if it's a favorite
        self.fav_label = QLabel("⭐" if is_favorite else "")
        self.fav_label.setStyleSheet("font-size: 10px;")

        time_label = QLabel(time_ago)
        time_label.setObjectName("TimeLabel")

        header_layout.addWidget(self.tag_label)
        header_layout.addWidget(self.fav_label)  # Added favorite indicator
        header_layout.addStretch()
        header_layout.addWidget(time_label)

        # Content: Single line with "..."
        self.content_label = QLabel()
        self.content_label.setObjectName("ContentLabel")

        layout.addLayout(header_layout)
        layout.addWidget(self.content_label)

    def paintEvent(self, event):
        metrics = QFontMetrics(self.content_label.font())
        display_text = self.raw_content.replace('\n', ' ').strip()
        # Adjusted width to account for the new star label
        elided = metrics.elidedText(display_text, Qt.ElideRight, self.width() - 40)
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
        """Updated to pull real data from the database columns"""
        self.list_widget.clear()

        # New DB returns: (id, content, tag, is_favorite, timestamp)
        items = get_recent_items(limit=15)

        for item in items:
            db_id = item[0]
            content = item[1]
            tag = item[2]
            is_fav = item[3]
            raw_time = item[4]

            # Use the helper function from your database file to get "5m ago"
            time_str = get_time_ago(raw_time)

            custom_widget = ClipboardItemWidget(
                content=content,
                category=tag,
                time_ago=time_str,
                is_favorite=is_fav
            )

            list_item = QListWidgetItem(self.list_widget)
            list_item.setSizeHint(custom_widget.sizeHint())

            self.list_widget.addItem(list_item)
            self.list_widget.setItemWidget(list_item, custom_widget)

    def copy_selection(self, item):
        widget = self.list_widget.itemWidget(item)
        pyperclip.copy(widget.raw_content)

        header_lbl = self.findChild(QLabel, "MainHeader")
        header_lbl.setText("✅ Copied!")
        header_lbl.setStyleSheet("color: #7aa2f7;")  # Briefly turn blue

        QTimer.singleShot(1000, lambda: self.reset_header())

    def reset_header(self):
        header_lbl = self.findChild(QLabel, "MainHeader")
        header_lbl.setText("🕒 Recent Copies")
        header_lbl.setStyleSheet("color: white;")

    def apply_styles(self):
        # (Styles remain largely the same, optimized for OLED black)
        self.setStyleSheet("""
            #Container { background-color: #000000; border-radius: 20px; border: 1px solid #222222; }
            #MainHeader { color: #ffffff; font-size: 15px; font-weight: 700; padding: 5px; }
            #HistoryList { background-color: transparent; border: none; outline: none; }
            #HistoryList::item { background-color: transparent; border: none; }
            #ItemCard { background-color: #0d0d0d; border-radius: 12px; border: 1px solid #1f1f1f; }
            #ItemCard:hover { background-color: #161616; border: 1px solid #333333; }
            #ContentLabel { color: #eeeeee; font-size: 13px; font-weight: 400; }
            #TimeLabel { color: #555555; font-size: 11px; }
            #TagCode { background-color: #311b47; color: #bb9af7; border-radius: 4px; padding: 2px 8px; font-size: 10px; font-weight: bold; }
            #TagURL { background-color: #1a273e; color: #7aa2f7; border-radius: 4px; padding: 2px 8px; font-size: 10px; font-weight: bold; }
            #TagText { background-color: #222222; color: #999999; border-radius: 4px; padding: 2px 8px; font-size: 10px; font-weight: bold; }
            #FooterLink { color: #3d59a1; font-size: 13px; font-weight: 600; padding-top: 15px; border-top: 1px solid #1a1a1a; }
            QScrollBar:vertical { border: none; background: transparent; width: 4px; }
            QScrollBar::handle:vertical { background: #333333; border-radius: 2px; }
        """)