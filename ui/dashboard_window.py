import pyperclip
from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QWidget, QScrollArea, QLineEdit,
                             QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QTimer, QPoint, QRect
from PyQt5.QtGui import QFont, QColor, QCursor
from themes.theme_manager import theme_engine
from ui.dashboard_card import ClipboardCard
from db.database import get_time_ago, get_recent_items, get_total_count
from ui.help_window import HelpWindow


class HistoryWindow(QWidget):
    def __init__(self, parent_window=None):
        super().__init__()
        self.parent_win = parent_window

        # 1. WINDOW SETUP
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # CRITICAL: Enable tracking for the window
        self.setMouseTracking(True)

        self.resize(1240, 880)
        self.search = QLineEdit()
        self.search.setObjectName("ModernSearch")
        # Ensure it doesn't have a default frame that might be capturing colors
        self.search.setFrame(False)
        # 2. RESIZE STATE
        self._drag_pos = None
        self._resize_edge = None
        self._margin = 10  # Slightly larger hit-box for easier grabbing
        self.current_filter = "ALL"
        self.settings_window = None

        # 3. MAIN LAYOUT
        self.main_layout = QVBoxLayout(self)
        # This padding creates the "dead zone" where the mouse hits the HistoryWindow
        # instead of the child widgets, allowing the resize cursor to appear.
        self.main_layout.setContentsMargins(self._margin, self._margin, self._margin, self._margin)

        # Background Shell
        self.shell = QFrame()
        self.shell.setObjectName("MainShell")

        # CRITICAL: The shell must also track the mouse or it will consume
        # the move events without telling the parent.
        self.shell.setMouseTracking(True)

        self.shell_layout = QHBoxLayout(self.shell)
        self.shell_layout.setContentsMargins(0, 0, 0, 0)
        self.shell_layout.setSpacing(0)
        self.main_layout.addWidget(self.shell)

        # --- Sidebar ---
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(280)
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(25, 45, 25, 30)

        self.logo = QLabel("CLIPPIE")
        self.logo.setObjectName("SidebarLogo")
        side_layout.addWidget(self.logo)
        side_layout.addSpacing(50)

        lbl_collections = QLabel("COLLECTIONS")
        lbl_collections.setObjectName("SectionLabel")
        side_layout.addWidget(lbl_collections)
        side_layout.addSpacing(15)

        # Filters
        self.filter_buttons = {}
        self.base_filters = [("ALL", "ALL", "All Clips"), ("★", "FAVORITES", "Favorites"),
                   ("TXT", "TEXT", "Plain Text"), ("</>", "CODE", "Source Code"),
                   ("🔗", "URL", "Web Links"), ("@ ", "EMAIL", "Emails"),
                   ("🖼", "IMAGE", "Images")]

        for icon, f_id, f_name in self.base_filters:
            btn = QPushButton(f"{icon}   {f_name} (0)")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setObjectName("SideNavBtn")
            btn.setFixedHeight(50)
            btn.clicked.connect(lambda checked, f=f_id: self.set_filter(f))
            side_layout.addWidget(btn)
            self.filter_buttons[f_id] = btn

        self.filter_buttons["ALL"].setChecked(True)
        side_layout.addStretch()

        # Sidebar Utilities
        util_frame = QFrame()
        util_layout = QHBoxLayout(util_frame)
        util_layout.setContentsMargins(0, 0, 0, 0)
        util_layout.setSpacing(12)

        self.btn_sync = self._create_util_btn("☁", "Cloud Sync")
        self.btn_settings = self._create_util_btn("⚙", "Settings")
        self.btn_help = self._create_util_btn("?", "Help")
        self.btn_settings.clicked.connect(self.open_settings)
        self.btn_help.clicked.connect(self.open_help)

        util_layout.addWidget(self.btn_sync)
        util_layout.addWidget(self.btn_settings)
        util_layout.addStretch()
        util_layout.addWidget(self.btn_help)
        side_layout.addWidget(util_frame)

        self.shell_layout.addWidget(self.sidebar)

        # --- Workspace ---
        self.workspace = QFrame()
        self.workspace.setObjectName("Workspace")
        self.workspace.setMouseTracking(True)  # Track mouse here too
        work_layout = QVBoxLayout(self.workspace)
        work_layout.setContentsMargins(0, 0, 0, 0)
        work_layout.setSpacing(0)

        # Top Bar
        self.top_nav = QFrame()
        self.top_nav.setFixedHeight(45)
        nav_layout = QHBoxLayout(self.top_nav)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.addStretch()

        self.btn_min = self._create_win_control("—", "Minimize")
        self.btn_max = self._create_win_control("▢", "Maximize")
        self.btn_close = self._create_win_control("✕", "Close", is_close=True)

        self.btn_min.clicked.connect(self.showMinimized)
        self.btn_max.clicked.connect(self.toggle_maximize)
        self.btn_close.clicked.connect(self.hide)

        nav_layout.addWidget(self.btn_min)
        nav_layout.addWidget(self.btn_max)
        nav_layout.addWidget(self.btn_close)
        work_layout.addWidget(self.top_nav)

        # Search Bar Area
        self.top_bar = QFrame()
        self.top_bar.setFixedHeight(100)
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(50, 0, 50, 0)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search your clipboard history...")
        self.search.setObjectName("ModernSearch")
        self.search.textChanged.connect(self.refresh_items)
        top_layout.addWidget(self.search)
        work_layout.addWidget(self.top_bar)

        # Content
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setObjectName("ContentScroll")
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.container = QWidget()
        self.container.setObjectName("ScrollContainer")
        self.cards_layout = QVBoxLayout(self.container)
        self.cards_layout.setContentsMargins(50, 0, 50, 50)
        self.cards_layout.setSpacing(20)
        self.cards_layout.setAlignment(Qt.AlignTop)

        self.scroll.setWidget(self.container)
        work_layout.addWidget(self.scroll)
        self.shell_layout.addWidget(self.workspace)

        theme_engine.theme_changed.connect(self.apply_theme)
        self.apply_theme(theme_engine.current_palette)

    # --- RE-SIZE ENGINE ---

    def _get_resize_edge(self, pos):
        w, h = self.width(), self.height()
        x, y = pos.x(), pos.y()
        m = self._margin

        # Check corners first
        if x < m and y < m: return Qt.TopLeftCorner
        if x > w - m and y < m: return Qt.TopRightCorner
        if x < m and y > h - m: return Qt.BottomLeftCorner
        if x > w - m and y > h - m: return Qt.BottomRightCorner
        # Check edges
        if x < m: return Qt.LeftEdge
        if x > w - m: return Qt.RightEdge
        if y < m: return Qt.TopEdge
        if y > h - m: return Qt.BottomEdge
        return None

    def mousePressEvent(self, e):
        edge = self._get_resize_edge(e.pos())
        if edge:
            self._resize_edge = edge
            e.accept()
        elif e.button() == Qt.LeftButton and e.y() < 60 and not self.isMaximized():
            self._drag_pos = e.globalPos() - self.frameGeometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e):
        # Always check for edge to update cursor
        edge = self._get_resize_edge(e.pos())

        if not e.buttons():
            if edge == Qt.LeftEdge or edge == Qt.RightEdge:
                self.setCursor(Qt.SizeHorCursor)
            elif edge == Qt.TopEdge or edge == Qt.BottomEdge:
                self.setCursor(Qt.SizeVerCursor)
            elif edge in (Qt.TopLeftCorner, Qt.BottomRightCorner):
                self.setCursor(Qt.SizeBDiagCursor)
            elif edge in (Qt.TopRightCorner, Qt.BottomLeftCorner):
                self.setCursor(Qt.SizeFDiagCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

        if self._resize_edge:
            self._handle_resize(e.globalPos())
        elif self._drag_pos:
            self.move(e.globalPos() - self._drag_pos)

        e.accept()

    def mouseReleaseEvent(self, e):
        self._drag_pos = None
        self._resize_edge = None
        self.setCursor(Qt.ArrowCursor)

    def _handle_resize(self, global_pos):
        geo = self.geometry()
        edge = self._resize_edge

        if edge == Qt.RightEdge:
            geo.setRight(global_pos.x())
        elif edge == Qt.LeftEdge:
            geo.setLeft(global_pos.x())
        elif edge == Qt.BottomEdge:
            geo.setBottom(global_pos.y())
        elif edge == Qt.TopEdge:
            geo.setTop(global_pos.y())
        elif edge == Qt.TopLeftCorner:
            geo.setTopLeft(global_pos)
        elif edge == Qt.TopRightCorner:
            geo.setTopRight(global_pos)
        elif edge == Qt.BottomLeftCorner:
            geo.setBottomLeft(global_pos)
        elif edge == Qt.BottomRightCorner:
            geo.setBottomRight(global_pos)

        if geo.width() >= 600 and geo.height() >= 400:
            self.setGeometry(geo)

    # --- UTILS ---

    def _create_util_btn(self, icon, hint):
        btn = QPushButton(icon)
        btn.setFixedSize(42, 42)
        btn.setObjectName("UtilBtn")
        btn.setToolTip(hint)
        btn.setCursor(Qt.PointingHandCursor)
        glow = QGraphicsDropShadowEffect(btn)
        glow.setBlurRadius(0)
        glow.setColor(QColor(theme_engine.current_palette['accent']))
        glow.setOffset(0, 0)
        btn.setGraphicsEffect(glow)
        btn.enterEvent = lambda e: glow.setBlurRadius(20)
        btn.leaveEvent = lambda e: glow.setBlurRadius(0)
        return btn

    def open_settings(self):
        if self.settings_window is None:
            from ui.settings_window import SettingsWindow
            self.settings_window = SettingsWindow(self)
        if self.settings_window.isHidden():
            rect = self.geometry()
            self.settings_window.move(
                rect.center().x() - self.settings_window.width() // 2,
                rect.center().y() - self.settings_window.height() // 2
            )
            self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()
        self.search.setFocus()

    def open_help(self):
        if not hasattr(self, 'help_win') or self.help_win is None:
            self.help_win = HelpWindow(self)

        self.help_win.show()  # This triggers showEvent and fixes the style
        self.help_win.raise_()

    def _create_win_control(self, icon, hint, is_close=False):
        btn = QPushButton(icon)
        btn.setFixedSize(46, 32)
        btn.setObjectName("WinControl" if not is_close else "WinClose")
        btn.setFont(QFont("Segoe UI", 10))
        return btn

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            self.btn_max.setText("▢")
            self.main_layout.setContentsMargins(self._margin, self._margin, self._margin, self._margin)
        else:
            self.main_layout.setContentsMargins(0, 0, 0, 0)
            self.showMaximized()
            self.btn_max.setText("❐")
        self.apply_theme(theme_engine.current_palette)

    def set_filter(self, filter_name):
        self.current_filter = filter_name
        for name, btn in self.filter_buttons.items():
            btn.setChecked(name == filter_name)
        self.refresh_items()

    def refresh_items(self):
        """
        Clears the current view and repopulates cards from the database.
        Called on filter change, search change, or card action (star/delete).
        """
        from db.database import get_category_counts
        counts = get_category_counts()
        for icon, f_id, f_name in getattr(self, 'base_filters', []):
            if f_id in self.filter_buttons:
                self.filter_buttons[f_id].setText(f"{icon}   {f_name} ({counts.get(f_id, 0)})")

        # 1. Clear existing cards safely
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # 2. Fetch fresh items from DB
        search_term = self.search.text()
        items = get_recent_items(
            limit=40,
            search_query=search_term,
            filter_type=self.current_filter,
            mode="dashboard"  # Keeps favorites at top
        )

        p = theme_engine.current_palette

        # 3. Create and add cards
        if not items:
            no_data = QLabel("No clipboard items found...")
            no_data.setStyleSheet(f"color: {p['text_dim']}; font-size: 18px; margin-top: 50px;")
            no_data.setAlignment(Qt.AlignCenter)
            self.cards_layout.addWidget(no_data)
        else:
            for idx, i in enumerate(items):
                # i[0]=id, i[1]=content, i[2]=tag, i[3]=is_fav, i[4]=timestamp
                card = ClipboardCard(
                    item_id=i[0],
                    category=i[2],
                    is_fav=i[3],
                    time_ago=get_time_ago(i[4]),
                    content=i[1],
                    parent=self,  # Crucial for auto-refresh
                    p=p,
                    delay_ms=idx * 40
                )
                self.cards_layout.addWidget(card)

        # 4. Add a stretch at the end to keep cards aligned to top
        self.cards_layout.addStretch()

    def apply_theme(self, p):
        radius = 0 if self.isMaximized() else 15
        from PyQt5.QtGui import QPalette  # Ensure this is available

        # 1. THE RESET
        self.search.setStyleSheet("")
        pal = self.search.palette()

        # 2. THE FIX: Use QPalette.Text (The Constant) not self.search.text (The Method)
        theme_text_color = QColor(p['text_main'])
        theme_dim_color = QColor(p['text_dim'])

        # This forces the internal typing color to match your theme
        pal.setColor(QPalette.Text, theme_text_color)
        pal.setColor(QPalette.WindowText, theme_text_color)
        pal.setColor(QPalette.Base, Qt.transparent)
        pal.setColor(QPalette.PlaceholderText, theme_dim_color)

        self.search.setPalette(pal)

        # 3. APPLY CSS
        self.setStyleSheet(f"""
            QWidget {{ 
                font-family: 'Segoe UI', 'Segoe UI Symbol', 'Segoe UI Emoji', sans-serif; 
            }}
            #MainShell {{ background: {p['main_bg']}; border-radius: {radius}px; border: 1px solid {p['card_border']}; }}
            #Sidebar {{ background: {p['card_bg']}; border-right: 1px solid {p['card_border']}; border-top-left-radius: {radius}px; border-bottom-left-radius: {radius}px; }}
            #SidebarLogo {{ color: {p['accent']}; font-size: 20px; font-weight: 900; letter-spacing: 5px; }}
            #SectionLabel {{ color: {p['text_dim']}; font-size: 11px; font-weight: 800; letter-spacing: 1.5px; }}

            #SideNavBtn {{ background: transparent; color: {p['text_main']}; border-radius: 10px; padding-left: 18px; text-align: left; font-size: 14px; font-weight: 600; border: none; }}
            #SideNavBtn:hover {{ background: {p['widget_bg']}; color: {p['accent']}; }}
            #SideNavBtn:checked {{ background: {p['accent']}; color: {p['main_bg']}; }}

            #UtilBtn {{ background: {p['widget_bg']}; color: {p['text_main']}; border-radius: 12px; border: 1px solid {p['card_border']}; font-size: 18px; }}
            #UtilBtn:hover {{ border: 1px solid {p['accent']}; color: {p['accent']}; }}

            #WinControl, #WinClose {{ background: transparent; color: {p['text_main']}; border: none; }}
            #WinControl:hover {{ background: {p['widget_bg']}; }}
            #WinClose:hover {{ background: #e81123; color: white; border-top-right-radius: {radius}px; }}

            #FavBtn, #EditBtn, #CopyBtn, #DelBtn {{ 
                background-color: transparent; 
                border: 1px solid transparent; 
                border-radius: 10px; 
                color: {p['text_dim']}44; 
                font-family: 'Segoe UI Symbol', 'Segoe UI Emoji', 'Segoe UI', sans-serif;
                font-size: 18px; 
                outline: none;
            }}

            #ModernSearch {{
                background: transparent;
                color: {p['text_main']};
                border: none;
                font-size: 26px;
                selection-background-color: {p['accent']};
                selection-color: {p['main_bg']};
            }}

            #ModernSearch::placeholder {{
                color: {p['text_dim']};
            }}

            #ContentScroll, #ScrollContainer {{ background: transparent; }}

            /* --- CLEAN SCROLLBAR (No white lines) --- */
            #ContentScroll QScrollBar:vertical {{ 
                background: transparent; 
                width: 4px; 
                margin: 0px;
            }}
            #ContentScroll QScrollBar::handle:vertical {{ 
                background: {p['card_border']}; 
                border-radius: 2px; 
                min-height: 40px;
            }}
            #ContentScroll QScrollBar::handle:vertical:hover {{ 
                background: {p['accent']}; 
            }}
            #ContentScroll QScrollBar::add-line:vertical, 
            #ContentScroll QScrollBar::sub-line:vertical,
            #ContentScroll QScrollBar::add-page:vertical, 
            #ContentScroll QScrollBar::sub-page:vertical {{
                background: none;
                border: none;
                height: 0px;
            }}
        """)

        # 4. FINAL POLISH
        self.search.style().unpolish(self.search)
        self.search.style().polish(self.search)
        self.search.update()
        self.refresh_items()