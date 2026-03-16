from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt5.QtCore import Qt, QPoint, QTimer


class FloatingButton(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        # 1. Setup Window: Frameless, Always on Top, and No Taskbar icon
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(60, 60)

        # 2. Create the Round UI
        self.layout = QVBoxLayout()
        self.label = QLabel("📋")  # You can replace this with a QPixmap icon later
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                background-color: #3498db;
                color: white;
                border-radius: 30px;
                font-size: 20px;
                border: 2px solid #2980b9;
            }
            QLabel:hover {
                background-color: #2980b9;
            }
        """)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

        # Move to bottom right of screen by default
        self.move(100, 100)

        # Timer to check if we should hide the main window
        self.hide_timer = QTimer()
        self.hide_timer.timeout.connect(self.check_mouse_pos)
        self.hide_timer.start(200)

    def enterEvent(self, event):
        """When mouse enters the round button, calculate side based on screen edge"""
        self.main_window.load_items()  # Refresh list

        # Get the current screen's available geometry (ignoring taskbars)
        screen_geo = QApplication.primaryScreen().availableGeometry()
        screen_width = screen_geo.width()

        # Dimensions
        main_width = self.main_window.width()
        icon_x = self.x()
        icon_width = self.width()

        # 1. Calculate the gap on the right
        space_on_right = screen_width - (icon_x + icon_width)

        # 2. Determine X position
        if space_on_right >= main_width + 10:
            # Enough space on the right: Show to the right
            target_x = icon_x + icon_width + 10
        else:
            # Not enough space: Show to the left
            target_x = icon_x - main_width - 10

        # 3. Handle vertical alignment (keep it within screen Y bounds)
        target_y = self.y()
        if target_y + self.main_window.height() > screen_geo.height():
            target_y = screen_geo.height() - self.main_window.height() - 10

        self.main_window.move(target_x, target_y)
        self.main_window.show()

    def check_mouse_pos(self):
        """Hide main window only if mouse is NOT over button AND NOT over main window"""
        if self.main_window.isVisible():
            if not self.underMouse() and not self.main_window.underMouse():
                self.main_window.hide()

    # Optional: Logic to drag the button around the screen
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.globalPos() - self.dragPos)
            self.dragPos = event.globalPos()
            event.accept()
