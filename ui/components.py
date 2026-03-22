import sys
import os
from PyQt5.QtWidgets import (QApplication, QFrame, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QScrollArea, QWidget,
                             QLineEdit, QComboBox, QAbstractButton, QListView, QMessageBox)
from PyQt5.QtCore import Qt, QPropertyAnimation, pyqtProperty, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QFont
from themes.themes import ThemePalette


class ToggleSwitch(QAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(60, 32)
        self._circle_pos = 4

    @pyqtProperty(int)
    def circle_pos(self): return self._circle_pos

    @circle_pos.setter
    def circle_pos(self, pos):
        self._circle_pos = pos
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        track_color = QColor("#7aa2f7") if self.isChecked() else QColor("#24283b")
        p.setBrush(track_color)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, 0, self.width(), self.height(), 16, 16)
        p.setBrush(QColor("#ffffff"))
        p.drawEllipse(self._circle_pos, 4, 24, 24)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        end_val = 32 if self.isChecked() else 4
        self.anim = QPropertyAnimation(self, b"circle_pos")
        self.anim.setDuration(250)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.setEndValue(end_val)
        self.anim.start()


class SettingsCard(QFrame):
    def __init__(self, title, description, widget=None, is_danger=False):
        super().__init__()
        self.setObjectName("Card")
        self.setFixedHeight(145)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(35, 25, 35, 25)
        layout.setSpacing(25)

        text_layout = QVBoxLayout()
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("color: #ffffff; font-size: 22px; font-weight: 700; background: transparent;")

        self.desc_lbl = QLabel(description)
        self.desc_lbl.setStyleSheet("color: #565f89; font-size: 16px; background: transparent;")
        self.desc_lbl.setWordWrap(True)

        text_layout.addWidget(self.title_lbl)
        text_layout.addWidget(self.desc_lbl)
        layout.addLayout(text_layout, 1)

        if widget:
            self.style_controls(widget, is_danger)
            layout.addWidget(widget, 0, Qt.AlignRight | Qt.AlignVCenter)

    def style_controls(self, widget, is_danger):
        """Your exact control styles kept intact"""
        if isinstance(widget, QComboBox):
            widget.setFixedWidth(260)
            widget.setFixedHeight(55)
            widget.setView(QListView())
            widget.setStyleSheet("""
                QComboBox {
                    background-color: #16161e; border: 2px solid #24283b; border-radius: 12px;
                    padding-left: 20px; color: #c0caf5; font-size: 16px; font-weight: 600;
                }
                QComboBox:hover { border: 2px solid #7aa2f7; background-color: #1f2335; }
                QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: top right; width: 40px; border-left-width: 0px; }
                QComboBox::down-arrow { image: none; border-left: 6px solid transparent; border-right: 6px solid transparent; border-top: 6px solid #7aa2f7; margin-top: 2px; }
                QComboBox QAbstractItemView {
                    background-color: #16161e; border: 2px solid #414868; border-radius: 12px;
                    selection-background-color: #24283b; selection-color: #7aa2f7; outline: 0px; color: #c0caf5;
                }
                QComboBox QAbstractItemView::item { min-height: 50px; padding-left: 20px; border: none; }
                QComboBox QAbstractItemView::item:hover { background-color: #1f2335; color: #7aa2f7; }
            """)
        elif isinstance(widget, QLineEdit):
            widget.setStyleSheet("""
                background-color: #16161e; border: 2px solid #24283b; border-radius: 12px; 
                padding: 10px 20px; color: #c0caf5; font-size: 16px;
            """)
        elif isinstance(widget, QPushButton):
            obj_name = "DeleteButton" if is_danger else "ActionButton"
            widget.setObjectName(obj_name)
            widget.setCursor(Qt.PointingHandCursor)
            widget.setMinimumWidth(160)
            widget.setFixedHeight(55)


# ==========================================
# 2. MAIN WINDOW (Integrating Row Logic)
# ==========================================

class SettingsWindow(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        # Internal state for themes

        self.themes = {
            "Dark OLED": ThemePalette.DARK_OLED,
            "Tokyo Night": ThemePalette.TOKYO_NIGHT,
            "Light Minimal": ThemePalette.LIGHT_MINIMAL,
            "System Sync": ThemePalette.DARK_OLED  # Default fallback
        }

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(900, 950)

        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("MainFrame")

        # Start with Dark OLED
        self.apply_base_styles(self.themes["Dark OLED"])

        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header Section (Updating colors dynamically via styles)
        self.header = QFrame()
        self.header.setFixedHeight(160)
        h_layout = QHBoxLayout(self.header)
        h_layout.setContentsMargins(50, 0, 50, 0)
        self.btn_back = QPushButton("←")
        self.btn_back.setFixedSize(65, 65)
        self.btn_back.setObjectName("ActionButton")
        self.btn_back.setStyleSheet("font-size: 28px;")
        if back_callback: self.btn_back.clicked.connect(back_callback)

        self.title_label = QLabel("Settings")
        self.title_label.setObjectName("MainTitle")
        self.title_label.setStyleSheet("font-size: 48px; font-weight: 800; margin-left: 25px;")

        h_layout.addWidget(self.btn_back)
        h_layout.addWidget(self.title_label)
        h_layout.addStretch()
        layout.addWidget(self.header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self.s_layout = QVBoxLayout(container)
        self.s_layout.setContentsMargins(50, 0, 50, 50)
        self.s_layout.setSpacing(18)
        self.s_layout.setAlignment(Qt.AlignTop)

        self.add_rows()

        scroll.setWidget(container)
        layout.addWidget(scroll)
        win_layout = QVBoxLayout(self)
        win_layout.addWidget(self.main_frame)

    def apply_base_styles(self, p):
        """Injected palette p into your exact style look"""
        self.main_frame.setStyleSheet(f"""
            #MainFrame {{ background-color: {p['main_bg']}; border-radius: 32px; border: 1px solid {p['card_border']}; }}
            #MainTitle {{ color: {p['text_main']}; }}
            #Card {{ background-color: {p['card_bg']}; border: 1px solid {p['card_border']}; border-radius: 24px; }}
            #Card:hover {{ border: 1px solid {p['card_hover_border']}; background-color: {p['card_hover_bg']}; }}

            #ActionButton, #DeleteButton {{
                background: {p['widget_bg']}; border: 2px solid {p['border_color']}; border-radius: 15px; 
                color: {p['text_dim']}; font-size: 15px; font-weight: bold;
            }}
            #ActionButton:hover {{ 
                background: rgba(122, 162, 247, 0.1); color: {p['accent']}; border: 2px solid {p['accent']}; 
            }}
            #DeleteButton:hover {{ 
                background: {p['danger_hover']}; color: {p['danger_text']}; border: 2px solid {p['danger_text']}; 
            }}

            QScrollBar:vertical {{ border: none; background: transparent; width: 8px; margin: 10px 2px 10px 2px; }}
            QScrollBar::handle:vertical {{ background: {p['scroll_handle']}; min-height: 30px; border-radius: 4px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

    def add_rows(self):
        # 1. Theme Selection
        theme_box = QComboBox()
        theme_box.addItems(["Dark OLED", "Light Minimal", "Tokyo Night", "System Sync"])
        # Connect the change logic
        theme_box.currentTextChanged.connect(self.handle_theme_change)

        self.s_layout.addWidget(
            SettingsCard("Appearance", "Select your preferred visual aesthetic or sync with OS.", theme_box))

        # 2. Startup
        self.s_layout.addWidget(
            SettingsCard("Launch on Startup", "Open the application automatically on login.", ToggleSwitch()))

        # 3. History
        limit_box = QComboBox()
        limit_box.addItems(["100 Items", "500 Items", "Unlimited"])
        self.s_layout.addWidget(SettingsCard("History Limit", "Maximum items preserved in the clipboard.", limit_box))

        # 4. Shortcut
        hotkey = QLineEdit("Ctrl + Shift + V")
        hotkey.setFixedWidth(260)
        self.s_layout.addWidget(SettingsCard("Global Shortcut", "Hotkey used to toggle the dashboard.", hotkey))

        # 5. Sync
        self.s_layout.addWidget(
            SettingsCard("Cloud Synchronization", "Encrypt and backup history to your account.", ToggleSwitch()))

        # 6. Danger Zone
        reset_btn = QPushButton("Clean all data")
        # reset_btn.clicked.connect(self.handle_factory_reset)
        self.s_layout.addWidget(
            SettingsCard("Danger Zone", "Irreversibly wipe all data and settings.", reset_btn, True))

        self.s_layout.addStretch()

    def handle_theme_change(self, theme_name):
        palette = self.themes.get(theme_name, ThemePalette.DARK_OLED)
        self.apply_base_styles(palette)

    def mousePressEvent(self, event):
        """Captures the initial click position"""
        if event.button() == Qt.LeftButton:
            # Calculate the offset between the mouse click and the top-left of the window
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Moves the window as the mouse drags"""
        if event.buttons() == Qt.LeftButton:
            # Move the window to the new position minus the initial offset
            self.move(event.globalPos() - self.drag_pos)
            event.accept()

