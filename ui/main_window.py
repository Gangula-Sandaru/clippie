import sys
import pyperclip
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QFrame, QApplication
from PyQt5.QtCore import Qt, QTimer
from db.database import get_recent_items, get_time_ago
from ui.main_card import ClipboardItemWidget


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        # Compact Window Config
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(340, 500)

        self.dashboard_win = None

        # Container
        self.container = QFrame(self)
        self.container.setObjectName("Container")
        self.container.setFixedSize(340, 500)

        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(20, 20, 20, 15)
        self.main_layout.setSpacing(12)

        # Header
        self.header = QLabel("🕒 Recent")
        self.header.setObjectName("MainHeader")
        self.main_layout.addWidget(self.header)

        # List
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("HistoryList")
        self.list_widget.setSpacing(8)
        self.list_widget.itemClicked.connect(self.copy_selection)
        self.main_layout.addWidget(self.list_widget)

        # Footer
        self.footer = QLabel("View All History →")
        self.footer.setAlignment(Qt.AlignCenter)
        self.footer.setObjectName("FooterLink")
        self.footer.setCursor(Qt.PointingHandCursor)
        self.footer.mousePressEvent = self.open_dashboard
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
        self.header.setText("✅ Copied!")
        self.header.setStyleSheet("color: #9ece6a;")
        QTimer.singleShot(1000, lambda: (
            self.header.setText("🕒 Recent"),
            self.header.setStyleSheet("color: #ffffff;")
        ))

    def open_dashboard(self, event):
        self.hide()
        QApplication.processEvents()
        if self.dashboard_win is None:
            from ui.dashboard_window import HistoryWindow
            self.dashboard_win = HistoryWindow(parent_window=self)
        self.dashboard_win.show()


    def apply_styles(self):
        self.setStyleSheet("""
            #Container { 
                background-color: #0b0e14; 
                border-radius: 24px; 
                border: 1px solid #1f2631; 
            }

            #MainHeader { 
                color: #ffffff; 
                font-size: 17px; 
                font-weight: 800; 
                padding-left: 5px; 
            }

            #HistoryList { 
                background: transparent; 
                border: none; 
                outline: none; 
            }

            /* Item Cards Style */
            #ItemCard { 
                background-color: #161b22; 
                border-radius: 16px; 
                border: 1px solid #1f2631; 
            }
            #ItemCard:hover { 
                background-color: #1f2335; 
                border: 1px solid #3d59a1; 
            }

            #ContentLabel { 
                color: #c0caf5; 
                font-size: 14px; 
                font-weight: 500; 
            }

            #TimeLabel { 
                color: #565f89; 
                font-size: 11px; 
                font-weight: 600; 
            }

            #CopyIcon { 
                color: #7aa2f7; 
                font-size: 16px; 
            }

            /* Category Chips */
            #TagTEXT, #TagURL, #TagCODE { 
                font-size: 10px; 
                font-weight: 800; 
                border-radius: 6px; 
                padding: 3px 8px; 
            }
            #TagTEXT { background-color: #222a39; color: #9aa3ce; }
            #TagURL { background-color: rgba(122, 162, 247, 0.15); color: #7aa2f7; }
            #TagCODE { background-color: rgba(187, 154, 247, 0.15); color: #bb9af7; }

            /* Footer Styles */
            #FooterLink { 
                color: #3d59a1; 
                font-size: 14px; 
                font-weight: 700; 
                padding: 12px; 
                border-top: 1px solid #1f2631;
                margin-top: 5px;
            }
            #FooterLink:hover { 
                color: #7aa2f7; 
                background-color: rgba(122, 162, 247, 0.05);
                border-radius: 12px;
            }

            /* Tooltip Style */
            QToolTip {
                background-color: #1a1b26;
                color: #c0caf5;
                border: 1px solid #3d59a1;
                padding: 6px;
                border-radius: 6px;
                font-size: 12px;
            }

            /* Scrollbar Style */
            QScrollBar:vertical { 
                border: none; 
                background: transparent; 
                width: 6px; 
            }
            QScrollBar::handle:vertical { 
                background: #24283b; 
                border-radius: 3px; 
            }
            QScrollBar::handle:vertical:hover { 
                background: #3d59a1; 
            }
        """)


