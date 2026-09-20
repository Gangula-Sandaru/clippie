import sys
from PyQt5.QtWidgets import (QWidget, QLabel, QHBoxLayout, QVBoxLayout,
                             QPushButton, QFrame, QGraphicsDropShadowEffect,
                             QGraphicsOpacityEffect, QApplication)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PyQt5.QtGui import QColor, QFont
from themes.theme_manager import theme_engine


class SensitiveToastNotification(QWidget):
    """
    Sleek, theme-aware floating on-screen toast notification.
    Appears at the bottom-right of the screen when sensitive data is copied,
    ensuring the user is always visibly alerted even if Windows Action Center
    or balloon notifications are disabled or muted.
    """
    _current_instance = None

    def __init__(self, category: str, message: str = ""):
        super().__init__()
        # Ensure only one toast exists at a time (replace previous)
        if SensitiveToastNotification._current_instance:
            try:
                SensitiveToastNotification._current_instance.close()
            except Exception:
                pass
        SensitiveToastNotification._current_instance = self

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self.toast_width = 380
        self.toast_height = 95
        self.setFixedSize(self.toast_width, self.toast_height)

        # Card container
        self.card = QFrame(self)
        self.card.setObjectName("ToastCard")
        self.card.setGeometry(10, 10, self.toast_width - 20, self.toast_height - 20)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.card.setGraphicsEffect(shadow)

        # Layout
        main_layout = QHBoxLayout(self.card)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(12)

        # Shield / Security Icon
        self.icon_lbl = QLabel("🛡️")
        self.icon_lbl.setStyleSheet("font-size: 28px; background: transparent;")
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.icon_lbl, 0, Qt.AlignVCenter)

        # Text column
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(3)

        self.title_lbl = QLabel("Sensitive Data Shield")
        self.title_lbl.setStyleSheet("font-size: 13px; font-weight: 700; background: transparent;")

        detail_text = message or f"Detected {category}. Clippie prevented saving to history."
        self.msg_lbl = QLabel(detail_text)
        self.msg_lbl.setStyleSheet("font-size: 11px; background: transparent;")
        self.msg_lbl.setWordWrap(True)

        text_layout.addWidget(self.title_lbl)
        text_layout.addWidget(self.msg_lbl)
        main_layout.addLayout(text_layout, 1)

        # Close button
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self.fade_out_and_close)
        main_layout.addWidget(self.close_btn, 0, Qt.AlignTop)

        self.apply_theme(theme_engine.current_palette)

        # Position at bottom-right corner of screen
        self.position_on_screen()

        # Opacity animation for fade in
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)

        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(250)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

        # Auto-dismiss timer (stay for 3.5 seconds)
        self.dismiss_timer = QTimer(self)
        self.dismiss_timer.setSingleShot(True)
        self.dismiss_timer.timeout.connect(self.fade_out_and_close)

    def position_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.right() - self.toast_width - 15
            y = geo.bottom() - self.toast_height - 15
            self.move(x, y)

    def apply_theme(self, p):
        self.card.setStyleSheet(f"""
            QFrame#ToastCard {{
                background-color: {p['card_bg']};
                border: 1px solid {p['accent']};
                border-radius: 12px;
            }}
        """)
        self.title_lbl.setStyleSheet(f"color: {p['accent']}; font-size: 13px; font-weight: 700; background: transparent;")
        self.msg_lbl.setStyleSheet(f"color: {p['text_main']}; font-size: 11px; background: transparent;")
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {p['text_dim']};
                border: none;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: {p['text_main']};
            }}
        """)

    def show_toast(self):
        self.show()
        self.raise_()
        self.anim.start()
        self.dismiss_timer.start(3500)

    def fade_out_and_close(self):
        self.dismiss_timer.stop()
        self.anim.stop()
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(300)
        self.anim.setStartValue(self.opacity_effect.opacity())
        self.anim.setEndValue(0.0)
        self.anim.setEasingCurve(QEasingCurve.InCubic)
        self.anim.finished.connect(self.close)
        self.anim.start()


def show_sensitive_toast(category: str, message: str = ""):
    """Helper function to create and show the sensitive toast from the Qt main thread."""
    toast = SensitiveToastNotification(category, message)
    toast.show_toast()
    return toast
