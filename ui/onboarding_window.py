from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QWidget, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
from themes.theme_manager import theme_engine
from app_config import config

class OnboardingWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(500, 360)
        
        self.current_step = 0

        self.steps = [
            {
                "title": "Welcome to Clippie! 🎉",
                "desc": "Your ultimate smart clipboard manager is ready.\\nLet's quickly review how to fly through your workflow.",
                "icon": "🚀"
            },
            {
                "title": "Double 'Ctrl' Magic",
                "desc": "Rapidly double-tap the Ctrl key anytime, anywhere to toggle the Clippie menu smoothly onto your screen.",
                "icon": "🕹️"
            },
            {
                "title": "The Floating Button",
                "desc": "Prefer the mouse? Hold 'Alt' (or your custom hotkey) and hover over the floating blue dot to peek at your history seamlessly.",
                "icon": "🔵"
            },
            {
                "title": "One-click Paste",
                "desc": "When the menu is open, just click on any text, link, or image to instantly paste it directly into your active window.",
                "icon": "⚡"
            },
            {
                "title": "Intelligent Auto-tags",
                "desc": "Clippie automatically detects and segments Emails, URLs, Code, and Images, sorting them nicely in your expanded Dashboard.",
                "icon": "🧠"
            }
        ]

        # Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        self.container = QWidget(self)
        self.container.setObjectName("OnboardContainer")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(30, 40, 30, 25)
        self.container_layout.setSpacing(15)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.container.setGraphicsEffect(shadow)

        self.main_layout.addWidget(self.container)

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFont(QFont("Segoe UI", 48))
        self.container_layout.addWidget(self.icon_label)

        self.title_label = QLabel()
        self.title_label.setObjectName("OnboardTitle")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setWordWrap(True)
        self.container_layout.addWidget(self.title_label)
        
        self.desc_label = QLabel()
        self.desc_label.setObjectName("OnboardDesc")
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setWordWrap(True)
        self.container_layout.addWidget(self.desc_label)

        self.container_layout.addStretch()

        btn_layout = QHBoxLayout()
        self.btn_skip = QPushButton("Skip")
        self.btn_skip.setObjectName("BtnSkip")
        self.btn_skip.setCursor(Qt.PointingHandCursor)
        self.btn_skip.setToolTip("Skip this entirely")
        self.btn_skip.clicked.connect(self.finish)
        
        self.btn_next = QPushButton("Next →")
        self.btn_next.setObjectName("BtnNext")
        self.btn_next.setCursor(Qt.PointingHandCursor)
        self.btn_next.setToolTip("Go to next tip")
        self.btn_next.clicked.connect(self.next_step)

        btn_layout.addWidget(self.btn_skip)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_next)
        
        self.container_layout.addLayout(btn_layout)

        theme_engine.theme_changed.connect(self.apply_theme)
        self.apply_theme(theme_engine.current_palette)
        
        self.update_ui()
        
        QTimer.singleShot(0, self.center_on_screen)

    def center_on_screen(self):
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def apply_theme(self, p):
        self.setStyleSheet(f"""
            #OnboardContainer {{
                background-color: {p['main_bg']};
                border-radius: 20px;
                border: 1px solid {p['card_border']};
            }}
            #OnboardTitle {{
                color: {p['text_main']};
                font-size: 22px;
                font-weight: bold;
            }}
            #OnboardDesc {{
                color: {p['text_dim']};
                font-size: 14px;
                line-height: 1.5;
            }}
            QPushButton {{
                padding: 8px 16px;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }}
            #BtnSkip {{
                background-color: transparent;
                color: {p['text_dim']};
                border: 1px solid transparent;
            }}
            #BtnSkip:hover {{
                color: {p['text_main']};
                background-color: {p['widget_bg']};
            }}
            #BtnNext {{
                background-color: {p['accent']};
                color: {p['main_bg']};
                border: none;
            }}
            #BtnNext:hover {{
                background-color: {p['text_main']};
            }}
        """)

    def update_ui(self):
        step = self.steps[self.current_step]
        self.title_label.setText(step["title"])
        self.desc_label.setText(step["desc"])
        self.icon_label.setText(step["icon"])

        if self.current_step == len(self.steps) - 1:
            self.btn_next.setText("Got it! ✓")
            self.btn_next.setToolTip("Start using Clippie!")
        else:
            self.btn_next.setText("Next →")

    def next_step(self):
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self.update_ui()
        else:
            self.finish()

    def finish(self):
        config.save_setting("first_run", False)
        self.accept()
