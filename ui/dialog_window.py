from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog, QGraphicsDropShadowEffect, QLabel, QHBoxLayout, QPushButton, QVBoxLayout, QFrame, QTextEdit

class EditDialog(QDialog):
    def __init__(self, content, p, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(600, 450)
        self.updated_content = content

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)

        self.content_frame = QFrame()
        self.content_frame.setObjectName("DialogFrame")
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(30, 25, 30, 25)
        self.content_layout.setSpacing(15)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 8)
        self.content_frame.setGraphicsEffect(shadow)

        self.title_lbl = QLabel("EDIT CLIP")
        self.title_lbl.setStyleSheet(f"color: {p['accent']}; font-weight: 900; letter-spacing: 2px; font-size: 13px;")

        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(content)
        self.text_edit.setObjectName("EditArea")

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.setContentsMargins(0, 10, 0, 0)

        self.btn_no = QPushButton("CANCEL")
        self.btn_yes = QPushButton("SAVE")
        self.btn_yes.setObjectName("YesBtn")

        for btn in [self.btn_no, self.btn_yes]:
            btn.setFixedSize(120, 42)
            btn.setCursor(Qt.PointingHandCursor)

        self.btn_yes.clicked.connect(self.save_and_accept)
        self.btn_no.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_no)
        btn_layout.addWidget(self.btn_yes)

        self.content_layout.addWidget(self.title_lbl)
        self.content_layout.addWidget(self.text_edit)
        self.content_layout.addLayout(btn_layout)
        self.main_layout.addWidget(self.content_frame)

        self.setStyleSheet(f"""
            #DialogFrame {{
                background-color: {p['widget_bg']};
                border: 1px solid {p['card_border']};
                border-radius: 20px;
            }}
            QLabel {{ background: transparent; }}
            #EditArea {{
                background-color: {p['main_bg']};
                color: {p['text_main']};
                border: 1px solid {p['card_border']};
                border-radius: 12px;
                padding: 15px;
                font-size: 14px;
            }}
            #EditArea:focus {{
                border: 1px solid {p['accent']};
            }}
            QPushButton {{
                background: {p['main_bg']};
                color: {p['text_dim']};
                border: 1px solid {p['card_border']};
                border-radius: 12px;
                font-weight: 800;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {p['card_hover_bg']};
                color: {p['text_main'] if 'text_main' in p else 'white'};
                border: 1px solid {p['accent']};
            }}
            
            /* --- CLEAN SCROLLBAR (No white lines) --- */
            QScrollBar:vertical {{
                background: {p['main_bg']};
                width: 4px;
                margin: 0px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {p['card_border']};
                border-radius: 2px;
                min-height: 40px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {p['accent']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
                height: 0px;
                border: none;
            }}
        """)

    def save_and_accept(self):
        self.updated_content = self.text_edit.toPlainText()
        self.accept()

class ModernDialog(QDialog):
    def __init__(self, title, message, p, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.result_status = False

        # Main Box
        self.layout = QVBoxLayout(self)
        self.content_frame = QFrame()
        self.content_frame.setObjectName("DialogFrame")
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.content_layout.setSpacing(20)

        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 5)
        self.content_frame.setGraphicsEffect(shadow)

        # Text
        self.title_lbl = QLabel(title.upper())
        self.title_lbl.setStyleSheet(f"color: {p['accent']}; font-weight: 900; letter-spacing: 2px; font-size: 12px;")

        self.msg_lbl = QLabel(message)
        self.msg_lbl.setWordWrap(True)
        self.msg_lbl.setStyleSheet(f"color: {p['text_main']}; font-size: 16px; font-weight: 400;")

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        self.btn_yes = QPushButton("DELETE")
        self.btn_no = QPushButton("CANCEL")

        for btn in [self.btn_yes, self.btn_no]:
            btn.setFixedSize(110, 40)
            btn.setCursor(Qt.PointingHandCursor)

        self.btn_yes.clicked.connect(self.accept_action)
        self.btn_no.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_no)
        btn_layout.addWidget(self.btn_yes)

        # Build UI
        self.content_layout.addWidget(self.title_lbl)
        self.content_layout.addWidget(self.msg_lbl)
        self.content_layout.addLayout(btn_layout)
        self.layout.addWidget(self.content_frame)

        self.setStyleSheet(f"""
            #DialogFrame {{
                background-color: {p['widget_bg']};
                border: 1px solid {p['card_border']};
                border-radius: 20px;
            }}
            QPushButton {{
                background: {p['main_bg']};
                color: {p['text_dim']};
                border: 1px solid {p['card_border']};
                border-radius: 10px;
                font-weight: 800;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {p['card_hover_bg']};
                color: {p['text_main']};
                border: 1px solid {p['accent']};
            }}
            #YesBtn {{
                background: #3D1A1A;
                color: #FF4B4B;
            }}
        """)
        # Specific styling for the delete button
        self.btn_yes.setObjectName("YesBtn")

    def accept_action(self):
        self.result_status = True
        self.accept()


class ModernDialogMain(QDialog):
    def __init__(self, title, message, p, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)  # Dialog for better modal behavior
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)  # Freeze the background window
        self.setFixedSize(450, 240)

        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)

        self.content_frame = QFrame()
        self.content_frame.setObjectName("DialogFrame")
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(30, 25, 30, 25)
        self.content_layout.setSpacing(15)

        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 8)
        self.content_frame.setGraphicsEffect(shadow)

        # Text Elements
        self.title_lbl = QLabel(title.upper())
        self.title_lbl.setStyleSheet(f"color: {p['accent']}; font-weight: 900; letter-spacing: 2px; font-size: 13px;")

        self.msg_lbl = QLabel(message)
        self.msg_lbl.setWordWrap(True)
        self.msg_lbl.setStyleSheet(f"color: {p['text_main']}; font-size: 15px; line-height: 22px;")

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.setContentsMargins(0, 10, 0, 0)

        self.btn_no = QPushButton("CANCEL")
        self.btn_yes = QPushButton("DELETE ALL")
        self.btn_yes.setObjectName("YesBtn")

        for btn in [self.btn_no, self.btn_yes]:
            btn.setFixedSize(120, 42)
            btn.setCursor(Qt.PointingHandCursor)

        self.btn_yes.clicked.connect(self.accept)
        self.btn_no.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_no)
        btn_layout.addWidget(self.btn_yes)

        # Build UI
        self.content_layout.addWidget(self.title_lbl)
        self.content_layout.addWidget(self.msg_lbl)
        self.content_layout.addStretch()
        self.content_layout.addLayout(btn_layout)
        self.main_layout.addWidget(self.content_frame)

        self.setStyleSheet(f"""
            #DialogFrame {{
                background-color: {p['widget_bg']};
                border: 1px solid {p['card_border']};
                border-radius: 20px;
            }}
            QLabel {{ background: transparent; }}
            QPushButton {{
                background: {p['main_bg']};
                color: {p['text_dim']};
                border: 1px solid {p['card_border']};
                border-radius: 12px;
                font-weight: 800;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {p['card_hover_bg']};
                color: {p['text_main'] if 'text_main' in p else 'white'};
                border: 1px solid {p['accent']};
            }}
            #YesBtn {{
                background: rgba(255, 75, 75, 0.15);
                color: #FF4B4B;
                border: 1px solid rgba(255, 75, 75, 0.3);
            }}
            #YesBtn:hover {{
                background: #FF4B4B;
                color: white;
            }}
        """)
