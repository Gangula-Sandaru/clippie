from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog, QGraphicsDropShadowEffect, QLabel, QHBoxLayout, QPushButton, QVBoxLayout, QFrame, QTextEdit, QLineEdit

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


class VaultPasswordDialog(QDialog):
    def __init__(self, mode="ENTER_PASSWORD", p=None, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.mode = mode  # "SET_PASSWORD" or "ENTER_PASSWORD"
        self.p = p or {}

        height = 360 if mode == "SET_PASSWORD" else 290
        self.setFixedSize(480, height)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)

        self.content_frame = QFrame()
        self.content_frame.setObjectName("DialogFrame")
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(30, 25, 30, 25)
        self.content_layout.setSpacing(12)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 8)
        self.content_frame.setGraphicsEffect(shadow)

        # Title
        title_text = "🔒  SET VAULT PASSWORD" if mode == "SET_PASSWORD" else "🔒  UNLOCK SECURE VAULT"
        self.title_lbl = QLabel(title_text)
        self.title_lbl.setStyleSheet(f"color: {p['accent']}; font-weight: 900; letter-spacing: 2px; font-size: 13px;")

        # Description
        desc_text = (
            "Create a master password to protect your confidential clips."
            if mode == "SET_PASSWORD"
            else "Enter your master password to view confidential clips."
        )
        self.desc_lbl = QLabel(desc_text)
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setStyleSheet(f"color: {p['text_dim']}; font-size: 13px;")

        # Inputs
        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.Password)
        self.pwd_input.setPlaceholderText("Master Password")
        self.pwd_input.setObjectName("VaultInput")

        if mode == "SET_PASSWORD":
            self.pwd_confirm = QLineEdit()
            self.pwd_confirm.setEchoMode(QLineEdit.Password)
            self.pwd_confirm.setPlaceholderText("Confirm Master Password")
            self.pwd_confirm.setObjectName("VaultInput")
            self.pwd_confirm.returnPressed.connect(self.handle_submit)
        else:
            self.pwd_confirm = None

        self.pwd_input.returnPressed.connect(self.handle_submit)

        # Error label
        self.err_lbl = QLabel("")
        self.err_lbl.setStyleSheet("color: #ff5370; font-size: 12px; font-weight: 600;")
        self.err_lbl.hide()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.setContentsMargins(0, 10, 0, 0)

        self.btn_cancel = QPushButton("CANCEL")
        btn_action_text = "SET PASSWORD" if mode == "SET_PASSWORD" else "UNLOCK"
        self.btn_submit = QPushButton(btn_action_text)
        self.btn_submit.setObjectName("SubmitBtn")

        for btn in [self.btn_cancel, self.btn_submit]:
            btn.setFixedSize(130, 42)
            btn.setCursor(Qt.PointingHandCursor)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_submit.clicked.connect(self.handle_submit)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_submit)

        # Build Layout
        self.content_layout.addWidget(self.title_lbl)
        self.content_layout.addWidget(self.desc_lbl)
        self.content_layout.addWidget(self.pwd_input)
        if self.pwd_confirm:
            self.content_layout.addWidget(self.pwd_confirm)
        self.content_layout.addWidget(self.err_lbl)
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
            #VaultInput {{
                background-color: {p['main_bg']};
                color: {p['text_main']};
                border: 1px solid {p['card_border']};
                border-radius: 12px;
                padding: 10px 14px;
                font-size: 14px;
            }}
            #VaultInput:focus {{
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
                color: {p['text_main']};
                border: 1px solid {p['accent']};
            }}
            #SubmitBtn {{
                background: {p['accent']};
                color: {p['main_bg']};
                border: 1px solid {p['accent']};
            }}
            #SubmitBtn:hover {{
                opacity: 0.9;
            }}
        """)

    def handle_submit(self):
        from utils.vault_storage import (
            set_vault_password,
            verify_vault_password,
            unlock_vault
        )
        pwd = self.pwd_input.text().strip()
        if self.mode == "SET_PASSWORD":
            confirm = self.pwd_confirm.text().strip() if self.pwd_confirm else ""
            if not pwd:
                self.show_error("Password cannot be empty.")
                return
            if len(pwd) < 4:
                self.show_error("Password must be at least 4 characters.")
                return
            if pwd != confirm:
                self.show_error("Passwords do not match. Please re-enter.")
                return
            if set_vault_password(pwd):
                unlock_vault()
                self.accept()
            else:
                self.show_error("Failed to save password. Please try again.")
        else:
            if not pwd:
                self.show_error("Please enter your password.")
                return
            if verify_vault_password(pwd):
                unlock_vault()
                self.accept()
            else:
                self.show_error("Incorrect password. Please try again.")
                self.pwd_input.selectAll()
                self.pwd_input.setFocus()

    def show_error(self, message):
        self.err_lbl.setText(message)
        self.err_lbl.show()
