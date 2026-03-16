import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame,
    QLineEdit, QScrollArea, QPushButton, QButtonGroup
)
from PyQt5.QtCore import Qt, QTimer
from db.database import get_time_ago, get_recent_items
from ui.clipboard_card import ClipboardCard


class HistoryWindow(QWidget):
    def __init__(self, parent_window=None):
        super().__init__()
        self.parent_win = parent_window
        self._drag_pos = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(1150, 850)

        # Root Wrapper for Rounded Window
        self.wrapper = QFrame(self)
        self.wrapper.setObjectName("MainWrapper")
        main_layout = QVBoxLayout(self.wrapper)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- TOP NAV BAR ---
        self.nav = QFrame()
        self.nav.setObjectName("NavBar")
        self.nav.setFixedHeight(190)
        nav_layout = QVBoxLayout(self.nav)
        nav_layout.setContentsMargins(50, 30, 50, 30)

        # Row 1: Title + Action Icons (Cloud, Gear) + Window Controls
        row1 = QHBoxLayout()
        self.title = QLabel("Clippie Dashboard")
        self.title.setObjectName("DashboardTitle")

        # New Feature Buttons with Hints
        self.btn_sync = QPushButton("☁")
        self.btn_sync.setToolTip("Sync to Cloud")

        self.btn_settings = QPushButton("⚙")
        self.btn_settings.setToolTip("Settings")

        # Window Controls with Hints
        self.btn_min = QPushButton("—")
        self.btn_min.setToolTip("Minimize")

        self.btn_close = QPushButton("✕")
        self.btn_close.setToolTip("Close")

        row1.addWidget(self.title)
        row1.addStretch()

        # Style and add icons to cluster
        for b in [self.btn_sync, self.btn_settings]:
            b.setFixedSize(44, 44)
            b.setObjectName("FeatureButton")
            b.setCursor(Qt.PointingHandCursor)
            row1.addWidget(b)

        for b in [self.btn_min, self.btn_close]:
            b.setFixedSize(44, 44)
            b.setObjectName("WinControl")
            b.setCursor(Qt.PointingHandCursor)
            row1.addWidget(b)

        nav_layout.addLayout(row1)

        # Row 2: Search Bar + Filter Chips
        row2 = QHBoxLayout()
        row2.setSpacing(15)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search your snippets...")
        self.search.setObjectName("ModernSearch")
        self.search.setFixedHeight(58)
        self.search.textChanged.connect(self.refresh_items)
        row2.addWidget(self.search, 3)

        self.filter_group = QButtonGroup(self)
        for f in ["All", "Favorites", "Text", "Code", "URL"]:
            btn = QPushButton(f)
            btn.setCheckable(True)
            btn.setObjectName("FilterChip")
            btn.setFixedHeight(58)
            if f == "All": btn.setChecked(True)
            btn.clicked.connect(self.refresh_items)
            self.filter_group.addButton(btn)
            row2.addWidget(btn)

        nav_layout.addLayout(row2)
        main_layout.addWidget(self.nav)

        # --- SCROLLABLE AREA ---
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName("DashboardScroll")

        self.container = QWidget()
        self.container.setObjectName("ScrollContent")
        self.cards_layout = QVBoxLayout(self.container)
        self.cards_layout.setContentsMargins(50, 30, 50, 50)
        self.cards_layout.setSpacing(28)
        self.cards_layout.setAlignment(Qt.AlignTop)

        self.scroll.setWidget(self.container)
        main_layout.addWidget(self.scroll)

        # Main assembly
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.wrapper)

        self.apply_full_styles()
        self.refresh_items()

        # Connect Logic
        self.btn_close.clicked.connect(self.hide)
        self.btn_min.clicked.connect(self.showMinimized)
        self.btn_sync.clicked.connect(lambda: print("Syncing with cloud..."))

    def refresh_items(self):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        items = get_recent_items()
        search_text = self.search.text().lower()
        active_filter = self.filter_group.checkedButton().text()

        delay = 0
        for i in items:
            item_id, content, tag, fav, timestamp = i
            if search_text and search_text not in content.lower(): continue
            if active_filter == "Favorites" and not fav: continue
            if active_filter not in ["All", "Favorites"] and tag != active_filter: continue

            card = ClipboardCard(item_id, tag, fav, get_time_ago(timestamp), content, self)
            self.cards_layout.addWidget(card)
            card.animate(delay)
            delay += 40

    def apply_full_styles(self):
        self.setStyleSheet("""
            #MainWrapper { background: #0b0e14; border: 1px solid #1f2631; border-radius: 30px; }
            #NavBar { background: #0d1117; border-bottom: 1px solid #1f2631; border-top-left-radius: 30px; border-top-right-radius: 30px; }
            #DashboardTitle { color: #7aa2f7; font-size: 30px; font-weight: 800; letter-spacing: -1px; }

            #ModernSearch { 
                background: #141923; border: 2px solid #1f2631; border-radius: 18px; 
                padding: 0 25px; color: white; font-size: 16px; 
            }
            #ModernSearch:focus { border-color: #3d59a1; background: #1a1b26; }

            #FilterChip { 
                background: #141923; border: 1px solid #1f2631; border-radius: 18px; 
                padding: 0 22px; color: #565f89; font-weight: 700; font-size: 14px;
            }
            #FilterChip:checked { background: rgba(61, 89, 161, 0.25); color: #7aa2f7; border-color: #3d59a1; }

            /* Feature Icons (Cloud/Settings) */
            #FeatureButton { background: transparent; border: none; border-radius: 22px; color: #565f89; font-size: 22px; }
            #FeatureButton:hover { background: rgba(122, 162, 247, 0.1); color: #7aa2f7; }

            #WinControl { background: transparent; border-radius: 12px; color: #565f89; font-size: 18px; }
            #WinControl:hover { background: #f7768e; color: white; }

            QScrollArea, #ScrollContent { border: none; background: transparent; }
            QScrollBar:vertical { background: transparent; width: 10px; margin-right: 5px; }
            QScrollBar::handle:vertical { background: #24283b; border-radius: 5px; min-height: 40px; }
            QScrollBar::handle:vertical:hover { background: #3d59a1; }

            /* Modern Styled Tooltip */
            QToolTip {
                background-color: #1a1b26;
                color: #c0caf5;
                border: 1px solid #3d59a1;
                padding: 6px;
                border-radius: 6px;
                font-family: 'Segoe UI';
                font-size: 12px;
            }
        """)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton and self._drag_pos:
            self.move(e.globalPos() - self._drag_pos)