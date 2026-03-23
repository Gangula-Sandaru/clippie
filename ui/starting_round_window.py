from PyQt5.QtWidgets import QWidget, QLabel, QApplication, QGraphicsDropShadowEffect, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPen
from utils.helpers import is_activation_key_pressed
import keyboard
import time


class RoundIconLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._angle = 0

    @pyqtProperty(float)
    def angle(self): return self._angle

    @angle.setter
    def angle(self, value):
        self._angle = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self._angle)
        painter.translate(-self.width() / 2, -self.height() / 2)

        blue_color = QColor("#2563eb")
        painter.setBrush(blue_color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, self.width(), self.height())

        painter.setPen(QPen(Qt.white, 2))
        painter.setBrush(blue_color)
        rect_size = 19
        painter.drawRoundedRect(26, 18, rect_size, rect_size, 4, 4)
        painter.drawRoundedRect(18, 26, rect_size, rect_size, 4, 4)


class FloatingButton(QWidget):
    double_ctrl_signal = pyqtSignal()
    esc_signal = pyqtSignal()

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(90, 90)

        self.last_ctrl_time = 0
        self.opened_via_hotkey = False
        keyboard.on_release_key("ctrl", self.on_ctrl_release)
        keyboard.on_release_key("esc", self.on_esc_release)
        self.double_ctrl_signal.connect(self.toggle_main_window_from_hotkey)
        self.esc_signal.connect(self.hide_main_window_from_esc)

        self.icon_label = RoundIconLabel(self)
        self.icon_label.setFixedSize(60, 60)
        self.icon_label.move(15, 15)

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0.3)
        self.icon_label.setGraphicsEffect(self.opacity_effect)

        self.anim_rot = QPropertyAnimation(self.icon_label, b"angle")
        self.anim_rot.setDuration(200)
        self.anim_rot.setEasingCurve(QEasingCurve.OutQuad)

        self.anim_fade = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim_fade.setDuration(150)

        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.update_state)
        self.monitor_timer.start(100)

    def on_esc_release(self, e):
        self.esc_signal.emit()

    def hide_main_window_from_esc(self):
        if self.main_window.isVisible() and not getattr(self.main_window, '_is_hiding', False):
            self.opened_via_hotkey = False
            if hasattr(self.main_window, 'smooth_hide'):
                self.main_window.smooth_hide()
            else:
                self.main_window.hide()
            self.anim_rot.stop()
            self.anim_rot.setEndValue(0)
            self.anim_rot.start()

    def on_ctrl_release(self, e):
        current_time = time.time()
        if current_time - self.last_ctrl_time < 0.3:
            self.last_ctrl_time = 0
            self.double_ctrl_signal.emit()
        else:
            self.last_ctrl_time = current_time

    def toggle_main_window_from_hotkey(self):
        if self.main_window.isVisible() and not getattr(self.main_window, '_is_hiding', False):
            self.opened_via_hotkey = False
            if hasattr(self.main_window, 'smooth_hide'):
                self.main_window.smooth_hide()
            else:
                self.main_window.hide()
            self.anim_rot.stop()
            self.anim_rot.setEndValue(0)
            self.anim_rot.start()
        else:
            self.opened_via_hotkey = True
            self.anim_rot.stop()
            self.anim_rot.setEndValue(5)
            self.anim_rot.start()

            self.main_window.load_items()
            screen = QApplication.primaryScreen().availableGeometry()

            if self.x() + self.width() + self.main_window.width() + 10 <= screen.right():
                target_x = self.x() + self.width() + 5
            else:
                target_x = self.x() - self.main_window.width() - 5

            from PyQt5.QtCore import QPoint
            if hasattr(self.main_window, 'smooth_show'):
                self.main_window.smooth_show(QPoint(target_x, self.y()))
            else:
                self.main_window.move(target_x, self.y())
                self.main_window.show()

    def update_state(self):
        # Strict check: Alt must be alone
        is_pressed_alone = is_activation_key_pressed()
        current_opacity = self.opacity_effect.opacity()

        if is_pressed_alone and current_opacity < 1.0:
            self.anim_fade.stop()
            self.anim_fade.setEndValue(1.0)
            self.anim_fade.start()
        elif not is_pressed_alone and current_opacity > 0.3 and not self.underMouse():
            self.anim_fade.stop()
            self.anim_fade.setEndValue(0.3)
            self.anim_fade.start()

        if self.main_window.isVisible():
            if getattr(self.main_window, 'is_locked', False) or getattr(self, 'opened_via_hotkey', False):
                pass  # Do not hide if it's explicitly locked open or hotkey toggled
            elif not self.underMouse() and not self.main_window.underMouse():
                if hasattr(self.main_window, 'smooth_hide'):
                    self.main_window.smooth_hide()
                else:
                    self.main_window.hide()
                self.anim_rot.stop()
                self.anim_rot.setEndValue(0)
                self.anim_rot.start()

    def enterEvent(self, event):
        # Only open if Alt is the ONLY key being pressed
        if is_activation_key_pressed():
            self.anim_rot.stop()
            self.anim_rot.setEndValue(5)
            self.anim_rot.start()

            self.main_window.load_items()
            screen = QApplication.primaryScreen().availableGeometry()

            if self.x() + self.width() + self.main_window.width() + 10 <= screen.right():
                target_x = self.x() + self.width() + 5
            else:
                target_x = self.x() - self.main_window.width() - 5

            from PyQt5.QtCore import QPoint
            if hasattr(self.main_window, 'smooth_show'):
                self.main_window.smooth_show(QPoint(target_x, self.y()))
            else:
                self.main_window.move(target_x, self.y())
                self.main_window.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: self.dragPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.globalPos() - self.dragPos)
            self.dragPos = event.globalPos()
