import sys
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt5.QtCore import Qt
from themes.theme_manager import theme_engine

class OCRWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.layout = QVBoxLayout()
        self.label = QLabel("OCR Mode Active")
        self.label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
        
        self.setFixedSize(140, 50)
        self.apply_theme(theme_engine.current_palette)
        theme_engine.theme_changed.connect(self.apply_theme)

    def apply_theme(self, p):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {p['card_bg']};
                border: 1px solid {p['accent']};
                border-radius: 8px;
            }}
            QLabel {{
                color: {p['text_main']};
                font-size: 14px;
                font-weight: bold;
                border: none;
                background: transparent;
            }}
        """)
