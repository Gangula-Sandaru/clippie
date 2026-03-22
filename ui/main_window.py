import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QListWidget,
                             QListWidgetItem, QFrame, QHBoxLayout, QGraphicsDropShadowEffect, QPushButton)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint
from PyQt5.QtGui import QColor
from themes.theme_manager import theme_engine


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        # Window Setup
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        # Reduced width for a thinner, modern look
        self.win_w, self.win_h = 340, 580
        self.setFixedSize(self.win_w, self.win_h)
        self.dashboard_win = None
        self.is_locked = False
        self._is_hiding = False

        # --- MAIN CONTAINER ---
        self.container = QFrame(self)
        self.container.setObjectName("Container")
        self.container.setFixedSize(self.win_w, self.win_h)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 120))
        self.container.setGraphicsEffect(shadow)

        # --- LAYOUT ---
        self.main_layout = QVBoxLayout(self.container)
        # Left: 15 (Thin side), Top: 25, Right: 5 (Scrollbar lane), Bottom: 15
        self.main_layout.setContentsMargins(15, 25, 5, 15)
        self.main_layout.setSpacing(12)

        # --- HEADER ---
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(5, 0, 15, 0)
        self.header = QLabel("Recent Clips")
        self.header.setObjectName("MainHeader")

        self.btn_lock = QPushButton("🔓")
        self.btn_lock.setObjectName("LockBtn")
        self.btn_lock.setFixedSize(24, 24)
        self.btn_lock.setCursor(Qt.PointingHandCursor)
        self.btn_lock.setCheckable(True)
        self.btn_lock.clicked.connect(self.toggle_lock)

        self.status_dot = QFrame()
        self.status_dot.setFixedSize(8, 8)
        self.status_dot.setObjectName("StatusDot")
        header_layout.addWidget(self.header)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_lock)
        header_layout.addWidget(self.status_dot)
        self.main_layout.addLayout(header_layout)
        self.header.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        # --- THE LIST ---
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("HistoryList")
        self.list_widget.setSelectionMode(QListWidget.NoSelection)
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.list_widget.setFocusPolicy(Qt.NoFocus)
        self.list_widget.setSpacing(8)
        self.list_widget.setFrameShape(QFrame.NoFrame)
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.main_layout.addWidget(self.list_widget)

        # --- FOOTER ---
        self.footer = QLabel("View all →")
        self.footer.setAlignment(Qt.AlignCenter)
        self.footer.setObjectName("FooterLink")
        self.footer.setFixedHeight(45)
        self.footer.setCursor(Qt.PointingHandCursor)
        self.footer.mousePressEvent = self.open_dashboard
        self.main_layout.addWidget(self.footer)

        theme_engine.theme_changed.connect(self.apply_styles)
        self.apply_styles(theme_engine.current_palette)

    def toggle_lock(self):
        if self.btn_lock.isChecked():
            self.btn_lock.setText("🔒")
            self.is_locked = True
        else:
            self.btn_lock.setText("🔓")
            self.is_locked = False

    def apply_styles(self, p):
        self.setStyleSheet(f"""
            #Container {{ 
                background-color: {p['main_bg']}; 
                border-radius: 28px; 
                border: 1px solid {p['card_border']}; 
            }}
            #MainHeader {{ 
                color: {p['text_main']}; 
                font-size: 19px; 
                font-weight: 800; 
                letter-spacing: -0.4px;
            }}
            #StatusDot {{ background-color: {p['accent']}; border-radius: 4px; }}

            #LockBtn {{
                background: transparent;
                border: none;
                color: {p['text_dim']};
                font-size: 14px;
            }}
            #LockBtn:hover {{
                color: {p['accent']};
            }}
            #LockBtn:checked {{
                color: {p['accent']};
            }}

            #HistoryList {{ 
                background: transparent; 
                border: none;
                outline: none;
                padding-right: 12px; 
            }}

            #FooterLink {{ 
                background-color: {p['widget_bg']};
                color: {p['accent']}; 
                font-size: 13px;
                font-weight: 700; 
                border-radius: 12px;
                margin-right: 10px;
            }}

            /* --- CLEAN SCROLLBAR (No white lines) --- */
            #HistoryList QScrollBar:vertical {{ 
                background: transparent; 
                width: 4px; 
                margin: 0px;
            }}

            #HistoryList QScrollBar::handle:vertical {{ 
                background: {p['card_border']}; 
                border-radius: 2px; 
                min-height: 40px;
            }}

            #HistoryList QScrollBar::handle:vertical:hover {{ 
                background: {p['accent']}; 
            }}

            /* This removes the 'white line' or background track */
            #HistoryList QScrollBar::add-line:vertical, 
            #HistoryList QScrollBar::sub-line:vertical,
            #HistoryList QScrollBar::add-page:vertical, 
            #HistoryList QScrollBar::sub-page:vertical {{
                background: none;
                border: none;
                height: 0px;
            }}
        """)
        self.load_items()

    def load_items(self):
        self.list_widget.clear()
        from db.database import get_recent_items, get_time_ago
        from ui.main_card import ClipboardItemWidget
        items = get_recent_items()
        p = theme_engine.current_palette

        for item in items:
            cw = ClipboardItemWidget(item[1], item[2], get_time_ago(item[4]), p)

            # Subtraction is key: List width - (Right Padding + Margin Buffer)
            cw.setFixedWidth(self.list_widget.width() - 28)

            li = QListWidgetItem(self.list_widget)
            li.setSizeHint(cw.sizeHint())
            self.list_widget.addItem(li)
            self.list_widget.setItemWidget(li, cw)

    def open_dashboard(self, event):
        if event.button() == Qt.LeftButton:
            self.hide()
            if self.dashboard_win is None:
                from ui.dashboard_window import HistoryWindow
                self.dashboard_win = HistoryWindow(parent_window=self)
            self.dashboard_win.show()

    def smooth_show(self, target_pos):
        if getattr(self, '_is_hiding', False) and hasattr(self, 'anim_fade'):
            self.anim_fade.stop()
        self._is_hiding = False
        
        self.setWindowOpacity(0.0)
        self.show() # Triggers showEvent to load items immediately
        
        # Slide offset 
        offset = -40 if target_pos.x() > self.pos().x() else 40
        start_x = target_pos.x() + offset
        self.move(start_x, target_pos.y())

        self.anim_fade = QPropertyAnimation(self, b"windowOpacity")
        self.anim_fade.setDuration(250)
        self.anim_fade.setStartValue(0.0)
        self.anim_fade.setEndValue(1.0)
        self.anim_fade.setEasingCurve(QEasingCurve.OutQuad)
        self.anim_fade.start()

        self.anim_slide = QPropertyAnimation(self, b"pos")
        self.anim_slide.setDuration(400)
        self.anim_slide.setStartValue(QPoint(start_x, target_pos.y()))
        self.anim_slide.setEndValue(target_pos)
        self.anim_slide.setEasingCurve(QEasingCurve.OutBack)
        self.anim_slide.start()

    def smooth_hide(self):
        if getattr(self, '_is_hiding', False) or not self.isVisible():
            return
        self._is_hiding = True
        
        self.anim_fade = QPropertyAnimation(self, b"windowOpacity")
        self.anim_fade.setDuration(200)
        self.anim_fade.setStartValue(self.windowOpacity())
        self.anim_fade.setEndValue(0.0)
        self.anim_fade.setEasingCurve(QEasingCurve.OutQuad)
        self.anim_fade.finished.connect(self._finish_hide)
        self.anim_fade.start()
        
    def _finish_hide(self):
        self.hide()
        self._is_hiding = False
        self.setWindowOpacity(1.0)

    def showEvent(self, event):
        super().showEvent(event)
        self.load_items()