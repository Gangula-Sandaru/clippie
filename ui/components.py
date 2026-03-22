from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QAbstractButton, QComboBox, QLineEdit, \
    QPushButton, QListView
from PyQt5.QtCore import Qt, QPropertyAnimation, pyqtProperty, QEasingCurve
from PyQt5.QtGui import QPainter, QColor


class ToggleSwitch(QAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(60, 32)
        self._circle_pos = 4

        # Initial default colors
        self.active_color = QColor("#7aa2f7")
        self.inactive_color = QColor("#24283b")
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
