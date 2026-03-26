from PyQt5.QtWidgets import (QWidget, QFrame, QHBoxLayout, QVBoxLayout, QLabel, QAbstractButton, 
                             QComboBox, QLineEdit, QPushButton, QListView)
from PyQt5.QtCore import Qt, QPropertyAnimation, pyqtProperty, QEasingCurve, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QKeySequence


class ToggleSwitch(QAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(60, 32)
        self._circle_pos = 32 if self.isChecked() else 4

        # Initial default colors
        self.active_color = QColor("#7aa2f7")
        self.inactive_color = QColor("#777777")
        self.knob_color = QColor("#ffffff")

    def set_theme_colors(self, active, inactive, knob):
        """Update colors from the palette and redraw"""
        self.active_color = QColor(active)
        self.inactive_color = QColor(inactive)
        self.knob_color = QColor(knob)
        self.update()

    @pyqtProperty(int)
    def circle_pos(self): return self._circle_pos

    @circle_pos.setter
    def circle_pos(self, pos):
        self._circle_pos = pos
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # Use dynamic colors instead of hardcoded hex strings
        bg_color = self.active_color if self.isChecked() else self.inactive_color

        p.setBrush(bg_color)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, 0, self.width(), self.height(), 16, 16)

        p.setBrush(self.knob_color)
        p.drawEllipse(self._circle_pos, 4, 24, 24)

    def setChecked(self, checked):
        super().setChecked(checked)
        self._circle_pos = 32 if checked else 4
        self.update()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        end_val = 32 if self.isChecked() else 4
        self.anim = QPropertyAnimation(self, b"circle_pos")
        self.anim.setDuration(200)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.anim.setEndValue(end_val)
        self.anim.start()


class SettingsCard(QFrame):
    def __init__(self, title, description, widget=None, is_danger=False):
        super().__init__()
        self.setObjectName("Card")
        self.setFixedHeight(145)
        self.is_danger = is_danger

        layout = QHBoxLayout(self)
        layout.setContentsMargins(35, 25, 35, 25)
        layout.setSpacing(25)

        text_layout = QVBoxLayout()
        self.title_lbl = QLabel(title)
        self.desc_lbl = QLabel(description)
        self.desc_lbl.setWordWrap(True)

        text_layout.addWidget(self.title_lbl)
        text_layout.addWidget(self.desc_lbl)
        layout.addLayout(text_layout, 1)

        self.widget = widget
        if widget:
            layout.addWidget(widget, 0, Qt.AlignRight | Qt.AlignVCenter)

    def update_theme(self, p):
        # Update Label colors
        self.title_lbl.setStyleSheet(
            f"color: {p['text_main']}; font-size: 22px; font-weight: 700; background: transparent;")
        self.desc_lbl.setStyleSheet(f"color: {p['text_dim']}; font-size: 16px; background: transparent;")

        if self.widget:
            # Check if this card's widget is the toggle switch
            if isinstance(self.widget, ToggleSwitch):
                self.widget.set_theme_colors(
                    active=p['accent'],
                    inactive=p['card_border'],  # Subtle background for off-state
                    knob="#ffffff" if p['main_bg'] == "#000000" else p['main_bg']
                    # White knob in dark, background color knob in light
                )

            # Apply standard styles for ComboBox/LineEdit
            self.style_controls(self.widget, p)

    def style_controls(self, widget, p):
        if isinstance(widget, QComboBox):
            widget.setFixedWidth(260)
            widget.setFixedHeight(55)
            widget.setView(QListView())
            widget.setStyleSheet(f"""
                QComboBox {{
                    background-color: {p['widget_bg']}; border: 2px solid {p['border_color']}; border-radius: 12px;
                    padding-left: 20px; color: {p['text_main']}; font-size: 16px; font-weight: 600;
                }}
                QComboBox:hover {{ border: 2px solid {p['accent']}; background-color: {p['card_hover_bg']}; }}
                QComboBox QAbstractItemView {{
                    background-color: {p['widget_bg']}; border: 2px solid {p['border_color']}; border-radius: 12px;
                    selection-background-color: {p['border_color']}; selection-color: {p['accent']}; color: {p['text_main']}; outline: 0px;
                }}
                QComboBox QAbstractItemView::item {{ min-height: 50px; padding-left: 20px; }}
            """)
        elif isinstance(widget, QLineEdit):
            widget.setStyleSheet(
                f"background-color: {p['widget_bg']}; border: 2px solid {p['border_color']}; border-radius: 12px; padding: 10px 20px; color: {p['text_main']}; font-size: 16px;")
        elif isinstance(widget, QPushButton):
            obj_name = "DeleteButton" if self.is_danger else "ActionButton"
            widget.setObjectName(obj_name)
            widget.setCursor(Qt.PointingHandCursor)
            widget.setMinimumWidth(160)
            widget.setFixedHeight(55)

class ShortcutsCard(QFrame):
    def __init__(self, p):
        super().__init__()
        self.setObjectName("Card")
        self.expanded = False
        self.setFixedHeight(120)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(35, 25, 35, 25)
        self.layout.setSpacing(0)

        # Header Row
        self.header_row = QHBoxLayout()
        text_layout = QVBoxLayout()
        self.title_lbl = QLabel("Keyboard Shortcuts")
        self.desc_lbl = QLabel("View and learn all global hotkeys.")
        text_layout.addWidget(self.title_lbl)
        text_layout.addWidget(self.desc_lbl)
        self.header_row.addLayout(text_layout)

        self.btn_toggle = QPushButton("View All")
        self.btn_toggle.setObjectName("ActionButton")
        self.btn_toggle.setFixedSize(140, 45)
        self.btn_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_toggle.clicked.connect(self.toggle_expand)
        self.header_row.addWidget(self.btn_toggle)

        self.layout.addLayout(self.header_row)

        # Content for shortcuts
        self.sc_container = QWidget()
        self.sc_container.hide()
        self.sc_layout = QVBoxLayout(self.sc_container)
        self.sc_layout.setContentsMargins(0, 20, 0, 0)
        self.sc_layout.setSpacing(15)

        self.add_shortcut("Double Ctrl", "Toggle the main history window.", p)
        self.add_shortcut("Esc Key", "Instantly hide any open window.", p)
        self.add_shortcut("Ctrl + Hold Ctrl", "Activate OCR Screen Capture tool.", p)
        self.add_shortcut("Hold Alt", "Quick-view recent clips on hover.", p)

        self.layout.addWidget(self.sc_container)
        self.update_theme(p)

    def add_shortcut(self, key, desc, p):
        row = QHBoxLayout()
        k_lbl = QLabel(key)
        k_lbl.setStyleSheet(f"color: {p['accent']}; font-weight: 800; font-size: 16px;")
        d_lbl = QLabel(desc)
        d_lbl.setStyleSheet(f"color: {p['text_dim']}; font-size: 15px;")
        row.addWidget(k_lbl)
        row.addStretch()
        row.addWidget(d_lbl)
        self.sc_layout.addLayout(row)

    def toggle_expand(self):
        self.expanded = not self.expanded
        self.sc_container.setVisible(self.expanded)
        self.btn_toggle.setText("Hide All" if self.expanded else "View All")
        self.setFixedHeight(340 if self.expanded else 120)
        # Force the parent container to resize
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(10, lambda: self.parent().adjustSize())

    def update_theme(self, p):
        self.title_lbl.setStyleSheet(f"color: {p['text_main']}; font-size: 22px; font-weight: 700; background: transparent;")
        self.desc_lbl.setStyleSheet(f"color: {p['text_dim']}; font-size: 16px; background: transparent;")
        self.setStyleSheet(f"QFrame#Card {{ background-color: {p['widget_bg']}; border: 1px solid {p['card_border']}; border-radius: 20px; }}")

class HotkeyRecorder(QPushButton):
    hotkey_changed = pyqtSignal(str)

    def __init__(self, current_val, p):
        super().__init__(current_val)
        self.setFixedSize(240, 55)
        self.is_recording = False
        self.setObjectName("ModernHotkey")
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(self.toggle_recording)
        self.update_theme(p)

    def toggle_recording(self):
        if not self.is_recording:
            self.is_recording = True
            self.setText("...")
            self.style().unpolish(self)
            self.style().polish(self)
        else:
            self.cancel_recording()

    def keyPressEvent(self, event):
        if not self.is_recording: return
        key = event.key()
        if key == Qt.Key_Escape:
            self.cancel_recording()
            return
        
        mod = event.modifiers()
        # Use PortableText to avoid system-specific surrogate characters
        seq = QKeySequence(mod | key).toString(QKeySequence.PortableText)
        if seq:
            # Normalize to lowercase and remove any non-ascii artifacts
            clean_seq = seq.lower().replace("ctrl+", "ctrl+").replace("alt+", "alt+").replace("shift+", "shift+")
            clean_seq = clean_seq.encode('ascii', 'ignore').decode('ascii').rstrip("+")
            
            # Prevent saving empty or incomplete hotkeys
            if clean_seq and not clean_seq.endswith("+"):
                self.setText(clean_seq)
                self.hotkey_changed.emit(clean_seq)
                self.is_recording = False
        
    def cancel_recording(self):
        self.is_recording = False
        self.setText(self.text())

    def update_theme(self, p):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {p['widget_bg']}; 
                border: 2px solid {p['card_border']};
                border-radius: 12px;
                color: {p['text_main']};
                font-size: 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{ border: 2px solid {p['accent']}; }}
        """)
