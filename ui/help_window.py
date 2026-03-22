from PyQt5.QtWidgets import (QWidget, QFrame, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QScrollArea, QGridLayout)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QFont, QColor
from themes.theme_manager import theme_engine


class HelpWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 1. WINDOW SETUP
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(700, 650)

        # State for dragging
        self._drag_pos = None

        # 2. MAIN LAYOUT
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        self.main_frame = QFrame()
        self.main_frame.setObjectName("HelpFrame")
        self.main_layout.addWidget(self.main_frame)

        self.inner_layout = QVBoxLayout(self.main_frame)
        self.inner_layout.setContentsMargins(0, 0, 0, 0)
        self.inner_layout.setSpacing(0)

        # 3. COMPONENTS
        self.setup_header()
        self.setup_content()

        # 4. THEME INITIALIZATION
        # We connect the signal, but we don't rely ONLY on __init__ for the first render
        theme_engine.theme_changed.connect(self.handle_theme_change)
        self.handle_theme_change(theme_engine.current_palette)

    def setup_header(self):
        self.header = QFrame()
        self.header.setFixedHeight(80)
        self.header.setObjectName("HelpHeader")
        h_layout = QHBoxLayout(self.header)
        h_layout.setContentsMargins(30, 0, 30, 0)

        self.title_lbl = QLabel("User Guide & Help")
        self.title_lbl.setObjectName("HelpTitle")
        # Secret: Let clicks pass through label so the header frame can handle dragging
        self.title_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(40, 40)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setObjectName("CloseBtn")
        self.btn_close.clicked.connect(self.hide)

        h_layout.addWidget(self.title_lbl)
        h_layout.addStretch()
        h_layout.addWidget(self.btn_close)
        self.inner_layout.addWidget(self.header)

    def setup_content(self):
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.viewport().setStyleSheet("background: transparent;")
        self.scroll.setObjectName("HelpScroll")

        self.container = QWidget()
        self.container.setObjectName("HelpContainer")
        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setContentsMargins(40, 20, 40, 40)
        self.content_layout.setSpacing(25)

        self.add_help_sections()

        self.scroll.setWidget(self.container)
        self.inner_layout.addWidget(self.scroll)

    def add_help_sections(self):
        # Section 1: Core Mechanics
        self.add_section("🚀 HOW TO USE CLIPPIE",
                         "1. Copy text normally (Ctrl+C). Clippie securely saves it in the background.\n"
                         "2. Press and hold the **Alt** key to reveal the floating Clippie button.\n"
                         "3. Hover over the circular button to smoothly slide out your recent clips.\n"
                         "4. **Click any clip** to instantly paste it directly into your active window!\n"
                         "5. Use the 🔓 Lock icon in the header to pin the panel open while pasting multiple items.")

        # Section 2: Dashboard
        self.add_section("⚙️ DASHBOARD & SETTINGS",
                         "Click 'View all →' at the bottom of the recent panel to open the full Dashboard.\n\n"
                         "• **Filter & Search**: Use the sidebar to instantly find and filter clips by Favorites, Code, URLs, or Emails.\n"
                         "• **Card Actions**: Click the ★ button to permanently Favorite a clip. Click the card body to expand long text.\n"
                         "• **Settings (⚙)**: Change visual themes (Dark OLED, Tokyo Night, etc.), set history size limits, wipe data, or use the Cloud Sync backup framework.")

        # Section 3: Smart Tagging
        self.add_section("🏷️ SMART CATEGORIES",
                         "Clips are automatically analyzed via regex and sorted into Categories:\n"
                         "• 🔗 URL: Website links and domains\n"
                         "• </> CODE: Programming snippets, brackets, and HTML\n"
                         "• @ EMAIL: Contact addresses\n"
                         "• TXT TEXT: General clipboard notes")

    def add_section(self, title, text):
        t_lbl = QLabel(title);
        t_lbl.setObjectName("SectionTitle")
        self.content_layout.addWidget(t_lbl)

        if text:
            m_lbl = QLabel(text);
            m_lbl.setWordWrap(True)
            m_lbl.setObjectName("HelpText")
            self.content_layout.addWidget(m_lbl)

    # --- THE CRITICAL FIXES ---

    def showEvent(self, event):
        """Forces a style refresh the moment the window becomes visible."""
        super().showEvent(event)
        self.handle_theme_change(theme_engine.current_palette)

    def handle_theme_change(self, p):
        """Applies theme colors. Targeted at QLabels to prevent black-on-black text."""
        self.setStyleSheet(f"""
            #HelpFrame {{ 
                background-color: {p['main_bg']}; 
                border-radius: 20px; 
                border: 1px solid {p['card_border']}; 
            }}

            /* Universal Label Fix: Ensures text is never black in dark themes */
            QLabel {{
                color: {p['text_main']};
                background: transparent;
            }}

            #HelpTitle {{ 
                font-size: 22px; 
                font-weight: 800;
            }}

            #SectionTitle {{ 
                color: {p['accent']}; 
                font-weight: 800; 
                font-size: 14px; 
                margin-top: 10px;
            }}

            #HelpText {{ 
                color: {p['text_dim']}; 
                font-size: 14px; 
                line-height: 20px;
            }}

            #KbdTag {{
                background: {p['widget_bg']}; 
                color: {p['accent']};
                padding: 4px 10px; 
                border-radius: 6px; 
                font-weight: bold;
                border: 1px solid {p['card_border']};
            }}

            #CloseBtn {{ 
                background: {p['widget_bg']}; 
                border: none; 
                border-radius: 10px; 
                color: {p['text_dim']}; 
                font-size: 16px;
            }}

            #CloseBtn:hover {{ 
                background: #e81123; 
                color: white; 
            }}

            /* Scrollbar Styling */
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {p['card_border']};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                background: none;
            }}
        """)

    # --- MOVEMENT ENGINE ---

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # We allow dragging from anywhere on the frame except the scroll area
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None