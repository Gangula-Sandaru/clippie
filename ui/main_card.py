from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics, QFont


class ClipboardItemWidget(QFrame):
    def __init__(self, content, category="Text", time_ago="Just now"):
        super().__init__()
        self.setObjectName("ItemCard")
        self.raw_content = content

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(6)

        # --- HEADER ---
        header = QHBoxLayout()

        # Category Tag
        self.tag_label = QLabel(category.upper())
        self.tag_label.setObjectName(f"Tag{category.upper()}")

        # Time Stamp
        self.time_label = QLabel(time_ago)
        self.time_label.setObjectName("TimeLabel")

        # Hover Copy Icon
        self.copy_icon = QLabel("❐")
        self.copy_icon.setObjectName("CopyIcon")
        self.copy_icon.setFixedSize(25, 25)
        self.copy_icon.setAlignment(Qt.AlignCenter)

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0.0)
        self.copy_icon.setGraphicsEffect(self.opacity_effect)

        header.addWidget(self.tag_label)
        header.addSpacing(8)
        header.addWidget(self.time_label)
        header.addStretch()
        header.addWidget(self.copy_icon)

        # --- CONTENT ---
        self.content_label = QLabel()
        self.content_label.setObjectName("ContentLabel")

        layout.addLayout(header)
        layout.addWidget(self.content_label)

    def enterEvent(self, event):
        self.opacity_effect.setOpacity(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.opacity_effect.setOpacity(0.0)
        super().leaveEvent(event)

    def paintEvent(self, event):
        """Forces text to take exactly 90% width then elide with '...'"""
        metrics = QFontMetrics(self.content_label.font())
        display_text = self.raw_content.replace('\n', ' ').strip()

        # Calculate 90% of current widget width
        target_width = int(self.width() * 0.9)
        elided = metrics.elidedText(display_text, Qt.ElideRight, target_width)

        self.content_label.setText(elided)
        super().paintEvent(event)