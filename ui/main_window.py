from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget
from db.database import get_recent_items
import pyperclip


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clippie History")
        self.setGeometry(100, 100, 400, 300)
        self.layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_items)
        self.layout.addWidget(self.refresh_button)

        self.setLayout(self.layout)
        self.load_items()

    def load_items(self):
        self.list_widget.clear()
        items = get_recent_items()
        for item in items:
            self.list_widget.addItem(item[1])  # item[1] is content

        # Allow click to copy back to clipboard
        self.list_widget.itemClicked.connect(self.copy_to_clipboard)

    def copy_to_clipboard(self, item):
        pyperclip.copy(item.text())
