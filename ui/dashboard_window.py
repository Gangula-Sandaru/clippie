import pyperclip
from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QWidget, QScrollArea, QLineEdit,
                             QGraphicsDropShadowEffect, QCalendarWidget, QDialog)
from PyQt5.QtCore import Qt, QTimer, QPoint, QRect, QDate, QEvent
from PyQt5.QtGui import QFont, QColor, QCursor, QPalette
from themes.theme_manager import theme_engine
from ui.dashboard_card import ClipboardCard
from db.database import get_time_ago, get_recent_items, get_total_count
from ui.help_window import HelpWindow


class CalendarPopup(QDialog):
    """
    Floating dark-themed calendar popup that automatically closes
    when clicking outside or when focus is lost.
    """
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_DeleteOnClose, False)

    def changeEvent(self, event):
        if event.type() == QEvent.ActivationChange and not self.isActiveWindow():
            self.reject()
        super().changeEvent(event)


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
        self.current_offset = 0
        self.is_loading = False
        self.has_more = True
        self._user_at_bottom = False  # True while user is pinned to the bottom
        self.current_date_filter = None  # Date filter key: "today", "yesterday", "this_week", "this_month", or None

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
                   ("🔒", "VAULT", "Secure Vault"),
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
        
        # Debounce timer for smooth search without freezing on large datasets
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(250)
        self.search_timer.timeout.connect(self.refresh_items)
        self.search.textChanged.connect(self.search_timer.start)
        
        top_layout.addWidget(self.search)
        work_layout.addWidget(self.top_bar)

        # Content — Section Header Bar (sticky, above scroll)
        self.section_header = QFrame()
        self.section_header.setObjectName("SectionHeader")
        self.section_header.setFixedHeight(52)
        sh_layout = QHBoxLayout(self.section_header)
        sh_layout.setContentsMargins(50, 0, 50, 0)

        self.section_title_lbl = QLabel("All Records")
        self.section_title_lbl.setObjectName("SectionTitle")

        self.section_count_lbl = QLabel("")
        self.section_count_lbl.setObjectName("SectionCount")

        self.btn_lock_vault = QPushButton("🔒 Lock Vault")
        self.btn_lock_vault.setObjectName("DateFilterBtn")
        self.btn_lock_vault.setFixedHeight(30)
        self.btn_lock_vault.setCursor(Qt.PointingHandCursor)
        self.btn_lock_vault.clicked.connect(self.lock_and_exit_vault)
        self.btn_lock_vault.hide()

        sh_layout.addWidget(self.section_title_lbl)
        sh_layout.addStretch()
        sh_layout.addWidget(self.btn_lock_vault)
        sh_layout.addWidget(self.section_count_lbl)
        work_layout.addWidget(self.section_header)

        # Date Filter Row — quick-filter buttons just below the section header
        self.date_filter_bar = QFrame()
        self.date_filter_bar.setObjectName("DateFilterBar")
        self.date_filter_bar.setFixedHeight(48)
        df_layout = QHBoxLayout(self.date_filter_bar)
        df_layout.setContentsMargins(50, 0, 50, 0)
        df_layout.setSpacing(10)

        self.date_filter_buttons = {}
        date_options = [
            (None,         "All Time"),
            ("today",      "Today"),
            ("yesterday",  "Yesterday"),
            ("this_week",  "This Week"),
            ("this_month", "This Month"),
        ]
        for key, label in date_options:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setObjectName("DateFilterBtn")
            btn.clicked.connect(lambda checked, k=key: self.set_date_filter(k))
            df_layout.addWidget(btn)
            self.date_filter_buttons[key] = btn

        # "All Time" is selected by default
        self.date_filter_buttons[None].setChecked(True)

        # Separator
        sep = QFrame()
        sep.setObjectName("DateFilterSep")
        sep.setFixedSize(1, 22)
        df_layout.addWidget(sep)

        # Calendar pick button
        self.btn_pick_date = QPushButton("📅  Pick Date")
        self.btn_pick_date.setCheckable(True)
        self.btn_pick_date.setCursor(Qt.PointingHandCursor)
        self.btn_pick_date.setObjectName("DateFilterBtn")
        self.btn_pick_date.clicked.connect(lambda _checked: self.show_calendar_picker())
        df_layout.addWidget(self.btn_pick_date)

        df_layout.addStretch()
        work_layout.addWidget(self.date_filter_bar)

        # Content — Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setObjectName("ContentScroll")
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.verticalScrollBar().valueChanged.connect(self.on_scroll)
        self.scroll.verticalScrollBar().rangeChanged.connect(lambda min_val, max_val: self.check_scroll_fill())

        self.container = QWidget()
        self.container.setObjectName("ScrollContainer")
        self.cards_layout = QVBoxLayout(self.container)
        self.cards_layout.setContentsMargins(50, 0, 50, 50)
        self.cards_layout.setSpacing(20)
        self.cards_layout.setAlignment(Qt.AlignTop)

        # Loading indicator (shown at bottom inside scroll container)
        self.loading_lbl = QLabel("⟳  Loading more…", self.container)
        self.loading_lbl.setObjectName("LoadingLabel")
        self.loading_lbl.setAlignment(Qt.AlignCenter)
        self.loading_lbl.setFixedHeight(48)
        self.loading_lbl.hide()

        # End-of-records footer
        self.end_lbl = QLabel("✦  All records loaded", self.container)
        self.end_lbl.setObjectName("EndLabel")
        self.end_lbl.setAlignment(Qt.AlignCenter)
        self.end_lbl.setFixedHeight(48)
        self.end_lbl.hide()

        self.cards_layout.addWidget(self.loading_lbl)
        self.cards_layout.addWidget(self.end_lbl)

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

    def lock_and_exit_vault(self):
        from utils.vault_storage import lock_vault
        lock_vault()
        self.set_filter("ALL")

    def hideEvent(self, event):
        from utils.vault_storage import lock_vault
        lock_vault()
        super().hideEvent(event)

    def set_filter(self, filter_name):
        if filter_name == "VAULT":
            from utils.vault_storage import is_vault_password_set, is_vault_unlocked
            if not is_vault_unlocked():
                from ui.dialog_window import VaultPasswordDialog
                mode = "ENTER_PASSWORD" if is_vault_password_set() else "SET_PASSWORD"
                p = theme_engine.current_palette
                dlg = VaultPasswordDialog(mode=mode, p=p, parent=self)
                geo = self.geometry()
                dlg.move(
                    geo.center().x() - dlg.width() // 2,
                    geo.center().y() - dlg.height() // 2
                )
                if not dlg.exec_():
                    # Revert button selection to current active filter
                    for name, btn in self.filter_buttons.items():
                        btn.setChecked(name == self.current_filter)
                    return

        self.current_filter = filter_name
        for name, btn in self.filter_buttons.items():
            btn.setChecked(name == filter_name)

        if hasattr(self, 'btn_lock_vault'):
            if filter_name == "VAULT":
                self.btn_lock_vault.show()
            else:
                self.btn_lock_vault.hide()

        self.refresh_items()

    def set_date_filter(self, date_key):
        """Called when a date quick-filter button is clicked (None = All Time)."""
        self.current_date_filter = date_key
        for key, btn in self.date_filter_buttons.items():
            btn.setChecked(key == date_key)
        # Uncheck / reset Pick Date button when a quick preset is chosen
        self.btn_pick_date.setChecked(False)
        self.btn_pick_date.setText("📅  Pick Date")
        self.refresh_items()

    def show_calendar_picker(self):
        """Opens a dark-themed calendar popup; applies the picked date as a custom filter."""
        p = theme_engine.current_palette

        dlg = CalendarPopup(self)
        dlg.setFixedSize(340, 360)

        outer = QFrame(dlg)
        outer.setObjectName("CalPickerShell")
        outer.setGeometry(0, 0, 340, 360)
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(14, 12, 14, 14)
        outer_layout.setSpacing(10)

        # ── Title row ──────────────────────────────────────
        title_row = QHBoxLayout()
        title_lbl = QLabel("Pick a Date", outer)
        title_lbl.setObjectName("CalPickerTitle")
        close_btn = QPushButton("✕", outer)
        close_btn.setObjectName("CalPickerClose")
        close_btn.setFixedSize(26, 26)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(dlg.reject)
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        title_row.addWidget(close_btn)
        outer_layout.addLayout(title_row)

        # ── Calendar ───────────────────────────────────────
        cal = QCalendarWidget(outer)
        cal.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        cal.setGridVisible(False)
        cal.setNavigationBarVisible(True)
        cal.setSelectedDate(QDate.currentDate())
        # Clicking any date directly accepts and closes
        cal.clicked.connect(lambda _d: dlg.accept())
        outer_layout.addWidget(cal)

        # ── Confirm button ─────────────────────────────────
        confirm_btn = QPushButton("Apply Date", outer)
        confirm_btn.setObjectName("CalPickerConfirm")
        confirm_btn.setCursor(Qt.PointingHandCursor)
        confirm_btn.setFixedHeight(36)
        confirm_btn.clicked.connect(dlg.accept)
        outer_layout.addWidget(confirm_btn)

        # ── Force dark palette on internal Qt calendar widgets ─
        cal_pal = cal.palette()
        c_bg = QColor(p.get("card_bg", "#16161e"))
        c_fg = QColor(p.get("text_main", "#ffffff"))
        c_dim = QColor(p.get("text_dim", "#565f89"))
        c_acc = QColor(p.get("accent", "#7aa2f7"))
        c_btn = QColor(p.get("widget_bg", "#1f2335"))
        cal_pal.setColor(QPalette.Window, c_bg)
        cal_pal.setColor(QPalette.WindowText, c_fg)
        cal_pal.setColor(QPalette.Base, c_bg)
        cal_pal.setColor(QPalette.AlternateBase, c_bg)
        cal_pal.setColor(QPalette.Text, c_fg)
        cal_pal.setColor(QPalette.Button, c_btn)
        cal_pal.setColor(QPalette.ButtonText, c_fg)
        cal_pal.setColor(QPalette.Highlight, c_acc)
        cal_pal.setColor(QPalette.HighlightedText, QColor("#000000"))
        cal.setPalette(cal_pal)

        # ── Stylesheet ─────────────────────────────────────
        dlg.setStyleSheet(f"""
            QDialog {{
                background-color: {p['card_bg']};
                border: 1px solid {p['card_border']};
                border-radius: 12px;
            }}
            #CalPickerShell {{
                background-color: {p['card_bg']};
                border: 1px solid {p['card_border']};
                border-radius: 12px;
            }}
            #CalPickerTitle {{
                color: {p['text_main']};
                font-size: 14px;
                font-weight: 700;
            }}
            #CalPickerClose {{
                background: transparent;
                color: {p['text_dim']};
                border: 1px solid {p['card_border']};
                font-size: 12px;
                border-radius: 13px;
                font-weight: 700;
            }}
            #CalPickerClose:hover {{ background: #f7768e; color: white; border-color: #f7768e; }}

            /* Full Dark Theme Calendar */
            QCalendarWidget {{
                background-color: {p['card_bg']};
            }}
            QCalendarWidget QWidget#qt_calendar_navigationbar {{
                background-color: {p['widget_bg']};
                border-radius: 8px;
                min-height: 36px;
            }}
            QCalendarWidget QToolButton {{
                color: {p['text_main']};
                background-color: transparent;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                margin: 2px 4px;
                padding: 4px 8px;
            }}
            QCalendarWidget QToolButton:hover {{
                background-color: {p['card_border']};
                color: {p['accent']};
            }}
            QCalendarWidget QToolButton:pressed {{
                background-color: {p['accent']};
                color: {p['main_bg']};
            }}
            QCalendarWidget QMenu {{
                background-color: {p['card_bg']};
                color: {p['text_main']};
                border: 1px solid {p['card_border']};
                border-radius: 6px;
                padding: 4px;
            }}
            QCalendarWidget QMenu::item:selected {{
                background-color: {p['accent']};
                color: {p['main_bg']};
                border-radius: 4px;
            }}
            QCalendarWidget QSpinBox {{
                background-color: {p['widget_bg']};
                color: {p['text_main']};
                border: 1px solid {p['card_border']};
                border-radius: 6px;
                padding: 2px 6px;
                selection-background-color: {p['accent']};
                selection-color: {p['main_bg']};
            }}
            QCalendarWidget QTableView {{
                background-color: {p['card_bg']};
                alternate-background-color: {p['card_bg']};
                selection-background-color: {p['accent']};
                selection-color: {p['main_bg']};
                color: {p['text_main']};
                border: none;
                outline: 0;
            }}
            QCalendarWidget QHeaderView {{
                background-color: {p['card_bg']};
            }}
            QCalendarWidget QHeaderView::section {{
                background-color: {p['card_bg']};
                color: {p['text_dim']};
                border: none;
                font-weight: 700;
                font-size: 11px;
                padding: 4px 0px;
            }}
            QCalendarWidget QAbstractItemView:enabled {{
                color: {p['text_main']};
                selection-background-color: {p['accent']};
                selection-color: {p['main_bg']};
            }}
            QCalendarWidget QAbstractItemView:disabled {{
                color: {p['text_dim']};
            }}

            #CalPickerConfirm {{
                background-color: {p['accent']};
                color: {p['main_bg']};
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 700;
            }}
            #CalPickerConfirm:hover {{
                background-color: {p['accent']};
                opacity: 0.85;
            }}
        """)

        # ── Position below the button ──────────────────────
        btn_global = self.btn_pick_date.mapToGlobal(QPoint(0, self.btn_pick_date.height() + 4))
        from PyQt5.QtWidgets import QApplication as _App
        screen_rect = _App.primaryScreen().availableGeometry()
        x = min(btn_global.x(), screen_rect.right() - 345)
        y = min(btn_global.y(), screen_rect.bottom() - 365)
        dlg.move(x, y)

        # ── Show ──────────────────────────────────────────
        if dlg.exec_() == QDialog.Accepted:
            q_date = cal.selectedDate()
            date_str = q_date.toString("yyyy-MM-dd")
            friendly = q_date.toString("MMM d, yyyy")
            self.current_date_filter = ("custom", date_str)
            for key, btn in self.date_filter_buttons.items():
                btn.setChecked(False)
            self.btn_pick_date.setChecked(True)
            self.btn_pick_date.setText(f"📅  {friendly}")
            self.refresh_items()
        else:
            is_custom = isinstance(self.current_date_filter, tuple)
            self.btn_pick_date.setChecked(is_custom)



    def _is_near_bottom(self):
        """True when the user is within trigger range of the bottom."""
        scrollbar = self.scroll.verticalScrollBar()
        max_val = scrollbar.maximum()
        value = scrollbar.value()
        if max_val <= 0:
            return False
        # Generous threshold: 2x viewport height or 800px so loading is continuous & seamless
        threshold = max(800, self.scroll.viewport().height() * 2)
        return value >= max_val - threshold

    def on_scroll(self, value):
        if self.is_loading or not self.has_more:
            return
        if self._is_near_bottom():
            self.load_more_items()

    def check_scroll_fill(self):
        """Keep loading until content fills or exceeds the viewport."""
        if not self.has_more or self.is_loading:
            return
        scrollbar = self.scroll.verticalScrollBar()
        if scrollbar.maximum() == 0 or self._is_near_bottom():
            self.load_more_items()

    def refresh_items(self):
        """
        Clears the current view and repopulates cards from the database.
        Called on filter change, search change, or card action (star/delete).
        """
        self.current_offset = 0
        self.has_more = True
        self.is_loading = True

        from db.database import get_category_counts
        counts = get_category_counts(date_filter=self.current_date_filter)
        for icon, f_id, f_name in getattr(self, 'base_filters', []):
            if f_id in self.filter_buttons:
                self.filter_buttons[f_id].setText(f"{icon}   {f_name} ({counts.get(f_id, 0)})")

        # Update section header title and count
        filter_labels = {
            "ALL": "All Records", "FAVORITES": "Favorites",
            "VAULT": "Secure Vault",
            "TEXT": "Plain Text", "CODE": "Source Code",
            "URL": "Web Links", "EMAIL": "Emails", "IMAGE": "Images",
        }
        title = filter_labels.get(self.current_filter, "All Records")
        total = counts.get(self.current_filter, 0)
        self.section_title_lbl.setText(title)
        self.section_count_lbl.setText(f"{total:,} items" if total else "")

        # 1. Clear existing items safely, keep loading_lbl and end_lbl
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            w = item.widget()
            if w:
                if w not in (self.loading_lbl, self.end_lbl):
                    w.deleteLater()

        # Hide footer labels
        self.loading_lbl.hide()
        self.end_lbl.hide()

        # 2. Fetch fresh items from DB or Separate Vault File
        search_term = self.search.text()
        limit = 50
        is_vault = (self.current_filter == "VAULT")

        if is_vault:
            from utils.vault_storage import get_vault_items
            vault_items = get_vault_items(search_term)
            items = [
                (v['id'], v['content'], v.get('category', 'Secure Vault'), 0, v['timestamp'], v.get('masked'))
                for v in vault_items
            ]
            items = items[self.current_offset: self.current_offset + limit]
        else:
            items = get_recent_items(
                limit=limit,
                offset=self.current_offset,
                search_query=search_term,
                filter_type=self.current_filter,
                mode="dashboard",  # Keeps favorites at top
                date_filter=self.current_date_filter,
            )

        p = theme_engine.current_palette

        # 3. Create and add cards
        if not items:
            msg = "Secure Vault is empty. Sensitive clips are automatically saved here." if is_vault else "No clipboard items found..."
            no_data = QLabel(msg)
            no_data.setStyleSheet(f"color: {p['text_dim']}; font-size: 18px; margin-top: 50px;")
            no_data.setAlignment(Qt.AlignCenter)
            self.cards_layout.addWidget(no_data)
            self.has_more = False
            self.section_count_lbl.setText("0 items")
        else:
            for idx, i in enumerate(items):
                # i[0]=id, i[1]=content, i[2]=tag, i[3]=is_fav, i[4]=timestamp, i[5]=masked
                masked_val = i[5] if is_vault and len(i) > 5 else None
                card = ClipboardCard(
                    item_id=i[0],
                    category=i[2],
                    is_fav=i[3],
                    time_ago=get_time_ago(i[4]),
                    content=i[1],
                    parent=self,  # Crucial for auto-refresh
                    p=p,
                    delay_ms=0,
                    is_vault=is_vault,
                    masked=masked_val
                )
                self.cards_layout.addWidget(card)
            
            self.current_offset += len(items)
            if len(items) < limit:
                self.has_more = False

        # Re-append footers and stretch at the bottom
        self.cards_layout.addWidget(self.loading_lbl)
        self.cards_layout.addWidget(self.end_lbl)
        self.cards_layout.addStretch()
        self.is_loading = False

        # Show end label immediately if all records fit in first batch
        if not self.has_more and items:
            self.end_lbl.show()

        # Trigger check in case the first batch doesn't fill the screen
        QTimer.singleShot(100, self.check_scroll_fill)


    def load_more_items(self):
        if self.is_loading or not self.has_more:
            return
            
        self.is_loading = True
        self.loading_lbl.show()
        self.end_lbl.hide()
        
        search_term = self.search.text()
        limit = 50
        is_vault = (self.current_filter == "VAULT")

        if is_vault:
            from utils.vault_storage import get_vault_items
            vault_items = get_vault_items(search_term)
            items = [
                (v['id'], v['content'], v.get('category', 'Secure Vault'), 0, v['timestamp'], v.get('masked'))
                for v in vault_items
            ]
            items = items[self.current_offset: self.current_offset + limit]
        else:
            items = get_recent_items(
                limit=limit,
                offset=self.current_offset,
                search_query=search_term,
                filter_type=self.current_filter,
                mode="dashboard",
                date_filter=self.current_date_filter,
            )
        
        if not items:
            self.has_more = False
            self.is_loading = False
            self.loading_lbl.hide()
            self.end_lbl.show()
            return
            
        # Temporarily remove stretch and footer widgets to append cards in proper sequence
        if self.cards_layout.count() > 0:
            last_item = self.cards_layout.itemAt(self.cards_layout.count() - 1)
            if last_item and last_item.spacerItem():
                self.cards_layout.removeItem(last_item)
        
        self.cards_layout.removeWidget(self.loading_lbl)
        self.cards_layout.removeWidget(self.end_lbl)
                
        p = theme_engine.current_palette
        
        for idx, i in enumerate(items):
            masked_val = i[5] if is_vault and len(i) > 5 else None
            card = ClipboardCard(
                item_id=i[0],
                category=i[2],
                is_fav=i[3],
                time_ago=get_time_ago(i[4]),
                content=i[1],
                parent=self,
                p=p,
                delay_ms=0,
                is_vault=is_vault,
                masked=masked_val
            )
            self.cards_layout.addWidget(card)
            
        self.current_offset += len(items)
        if len(items) < limit:
            self.has_more = False
            
        self.cards_layout.addWidget(self.loading_lbl)
        self.cards_layout.addWidget(self.end_lbl)
        self.cards_layout.addStretch()
        self.is_loading = False
        self.loading_lbl.hide()

        if not self.has_more:
            self.end_lbl.show()
        else:
            # Check if still near bottom to seamlessly chain more chunks
            QTimer.singleShot(100, self._post_load_check)

    def _post_load_check(self):
        """Called shortly after a chunk loads to keep filling if needed."""
        if self.has_more and not self.is_loading and self._is_near_bottom():
            self.load_more_items()

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

            /* --- SECTION HEADER --- */
            #SectionHeader {{ background: transparent; border-bottom: 1px solid {p['card_border']}; }}
            #SectionTitle {{ color: {p['text_main']}; font-size: 18px; font-weight: 700; }}
            #SectionCount {{ color: {p['text_dim']}; font-size: 13px; font-weight: 500; background: {p['widget_bg']}; border: 1px solid {p['card_border']}; border-radius: 10px; padding: 2px 12px; }}

            /* --- DATE FILTER BAR --- */
            #DateFilterBar {{ background: transparent; border-bottom: 1px solid {p['card_border']}; }}
            #DateFilterSep {{ background: {p['card_border']}; }}
            #DateFilterBtn {{
                background: transparent;
                color: {p['text_dim']};
                border: 1px solid {p['card_border']};
                border-radius: 14px;
                padding: 4px 14px;
                font-size: 12px;
                font-weight: 600;
            }}
            #DateFilterBtn:hover {{
                background: {p['widget_bg']};
                color: {p['text_main']};
                border: 1px solid {p['accent']};
            }}
            #DateFilterBtn:checked {{
                background: {p['accent']};
                color: {p['main_bg']};
                border: 1px solid {p['accent']};
            }}

            /* --- INFINITE SCROLL FOOTER LABELS --- */
            #LoadingLabel {{ color: {p['accent']}; font-size: 14px; font-weight: 600; background: transparent; }}
            #EndLabel {{ color: {p['text_dim']}; font-size: 13px; background: transparent; }}

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