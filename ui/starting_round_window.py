from PyQt5.QtWidgets import QWidget, QLabel, QApplication, QGraphicsDropShadowEffect, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QColor, QPainter, QPen
import keyboard


def is_activation_key_pressed():
    """Checks if Alt is pressed alone without common combo keys"""
    if not keyboard.is_pressed('alt'):
        return False

    # Prevent activation during Alt+Tab, Alt+F4, etc.
    forbidden_combos = ['tab', 'f4', 'shift', 'ctrl', 'space']
    if any(keyboard.is_pressed(k) for k in forbidden_combos):
        return False

    return True


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
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(90, 90)

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
            if not self.underMouse() and not self.main_window.underMouse():
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

            self.main_window.move(target_x, self.y())
            self.main_window.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: self.dragPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.globalPos() - self.dragPos)
            self.dragPos = event.globalPos()