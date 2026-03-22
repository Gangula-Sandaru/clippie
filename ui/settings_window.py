import pyperclip
from PyQt5.QtWidgets import (QWidget, QFrame, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QScrollArea, QComboBox, QLineEdit, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCursor

from app_config import config
from themes.theme_manager import theme_engine
from ui.components import SettingsCard, ToggleSwitch
from db.database import clear_all_data
from ui.dashboard_window import HistoryWindow
from ui.dialog_window import ModernDialog
from utils.startup_manager import set_startup
from utils.cloud_sync import sync_data_to_cloud


class SettingsWindow(QWidget):
    def __init__(self, parent=None, back_callback=None):
        super().__init__(parent)

        # 1. WINDOW SETUP
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.resize(900, 850)

        # 2. STATE
        self._drag_pos = None
        self._resize_edge = None
        self._margin = 10

        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(self._margin, self._margin, self._margin, self._margin)

        self.main_frame = QFrame()
        self.main_frame.setObjectName("MainFrame")
        self.main_frame.setMouseTracking(True)
        self.main_layout.addWidget(self.main_frame)

        self.inner_layout = QVBoxLayout(self.main_frame)
        self.inner_layout.setContentsMargins(0, 0, 0, 0)
        self.inner_layout.setSpacing(0)

        # --- HEADER ---
        self.setup_header(back_callback)

        # --- CONTENT AREA ---
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # FIX: Ensure the viewport of the scroll area is also transparent
        self.scroll.viewport().setStyleSheet("background: transparent;")

        self.container = QWidget()
        self.container.setObjectName("ScrollContainer")
        self.s_layout = QVBoxLayout(self.container)
        self.s_layout.setContentsMargins(50, 0, 50, 50)
        self.s_layout.setSpacing(18)
        self.s_layout.setAlignment(Qt.AlignTop)

        # Initialize Rows
        self.add_rows()

        self.scroll.setWidget(self.container)
        self.inner_layout.addWidget(self.scroll)

        # --- THEME INITIALIZATION ---
        theme_engine.theme_changed.connect(self.handle_theme_change)

        # FIX: Use QTimer to ensure style is applied after the widget is fully ready
        QTimer.singleShot(0, lambda: self.handle_theme_change(theme_engine.current_palette))

    def setup_header(self, back_callback):
        self.header = QFrame()
        self.header.setFixedHeight(120)
        h_layout = QHBoxLayout(self.header)
        h_layout.setContentsMargins(50, 0, 50, 0)

        self.btn_back = QPushButton("←")
        self.btn_back.setFixedSize(55, 55)
        self.btn_back.setObjectName("ActionButton")
        self.btn_back.setCursor(Qt.PointingHandCursor)

        if back_callback:
            self.btn_back.clicked.connect(back_callback)
        else:
            self.btn_back.clicked.connect(self.hide)

        self.title_label = QLabel("Settings")
        self.title_label.setObjectName("MainTitle")
        self.title_label.setStyleSheet("font-size: 38px; font-weight: 800; margin-left: 20px;")

        h_layout.addWidget(self.btn_back)
        h_layout.addWidget(self.title_label)
        h_layout.addStretch()
        self.inner_layout.addWidget(self.header)

    def add_rows(self):
        """Populate settings and connect them to the config and system logic."""

        # 1. Appearance
        theme_box = QComboBox()
        theme_box.setObjectName("ModernCombo")
        theme_box.addItems(["Dark OLED", "Tokyo Night", "Light Minimal"])
        theme_box.blockSignals(True)
        theme_box.setCurrentText(config.settings.get("theme", "Dark OLED"))
        theme_box.blockSignals(False)
        theme_box.currentTextChanged.connect(lambda v: config.save_setting("theme", v))
        theme_box.currentTextChanged.connect(theme_engine.set_theme)
        self.s_layout.addWidget(SettingsCard("Appearance", "Select your visual aesthetic.", theme_box))

        # 2. History Limit
        limit_box = QComboBox()
        limit_box.setObjectName("ModernCombo")
        limit_box.setFixedWidth(240)
        limit_box.addItems(["50 Records", "100 Records", "1000 Records", "Unlimited"])
        limit_box.blockSignals(True)
        limit_box.setCurrentText(config.settings.get("history_limit", "100 Records"))
        limit_box.blockSignals(False)
        limit_box.currentTextChanged.connect(lambda v: config.save_setting("history_limit", v))
        self.s_layout.addWidget(SettingsCard("History Limit", "Automatically cleanup older clips.", limit_box))

        # 3. Startup Toggle
        startup_sw = ToggleSwitch()
        is_startup = config.settings.get("startup", True)
        startup_sw.setChecked(is_startup)

        def handle_startup_toggle():
            state = startup_sw.isChecked()
            config.save_setting("startup", state)
            set_startup(state)

        startup_sw.clicked.connect(handle_startup_toggle)
        self.s_layout.addWidget(SettingsCard("Launch on Startup", "Open automatically on pc login.", startup_sw))

        # 4. Shortcut Input
        hotkey = QLineEdit()
        hotkey.setFixedWidth(240)
        hotkey.setObjectName("ModernInput")
        hotkey.setText(config.settings.get("hotkey", "alt"))
        hotkey.editingFinished.connect(lambda: config.save_setting("hotkey", hotkey.text()))
        self.s_layout.addWidget(SettingsCard("Global Shortcut", "Hotkey to toggle dashboard.", hotkey))

        # 5. Cloud Sync Toggle
        cloud_sw = ToggleSwitch()
        cloud_sw.setChecked(config.settings.get("cloud_sync", False))
        cloud_sw.clicked.connect(lambda: config.save_setting("cloud_sync", cloud_sw.isChecked()))
        self.s_layout.addWidget(SettingsCard("Enable Cloud Sync", "Automatically backup clips to the cloud.", cloud_sw))

        # 6. Manual Sync Button
        self.sync_btn = QPushButton("Sync Now")
        self.sync_btn.setObjectName("ActionButton")
        self.sync_btn.setFixedSize(180, 45)
        self.sync_btn.setCursor(Qt.PointingHandCursor)
        self.sync_btn.clicked.connect(self.handle_manual_sync)
        self.s_layout.addWidget(SettingsCard("Manual Sync", "Force backup to the server now.", self.sync_btn))

        # 5. Danger Zone
        self.reset_btn = QPushButton("Clean all data")
        self.reset_btn.setObjectName("DeleteButton")
        self.reset_btn.setFixedSize(180, 45)
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.clicked.connect(self.handle_data_reset)
        self.s_layout.addWidget(SettingsCard("Danger Zone", "Irreversibly wipe all data.", self.reset_btn))

        self.s_layout.addStretch()

    def handle_manual_sync(self):
        self.sync_btn.setText("Syncing...")
        self.sync_btn.setEnabled(False)

        def on_success():
            self.sync_btn.setText("Sync Done!")
            QTimer.singleShot(2000, lambda: self.reset_sync_button())
            
        def on_error(err):
            self.sync_btn.setText("Sync Failed!")
            print(f"Cloud Sync Error: {err}")
            QTimer.singleShot(2000, lambda: self.reset_sync_button())
            
        sync_data_to_cloud(on_success, on_error)
        
    def reset_sync_button(self):
        self.sync_btn.setText("Sync Now")
        self.sync_btn.setEnabled(True)

    def handle_data_reset(self):
        """Replaces QMessageBox with your new ModernDialog."""
        p = theme_engine.current_palette

        # Initialize the dialog
        dialog = ModernDialog(
            "Confirm Data Wipe",
            "Are you sure you want to delete all history? This action is irreversible and will empty your dashboard.",
            p,
            self  # Setting parent allows centering
        )

        # Center the dialog manually relative to the SettingsWindow
        dialog.move(
            self.x() + (self.width() - dialog.width()) // 2,
            self.y() + (self.height() - dialog.height()) // 2
        )

        # If user clicks DELETE (self.accept())
        if dialog.exec_():
            clear_all_data()
            refresh = HistoryWindow()
            refresh.refresh_items()
            self.reset_btn.setText("Data Wiped!")
            self.reset_btn.setEnabled(False)
            QTimer.singleShot(3000, lambda: (self.reset_btn.setText("Clean all data"), self.reset_btn.setEnabled(True)))

    def handle_theme_change(self, palette):
        """Applies the color palette and fixes background bleeding issues."""
        self.setStyleSheet("background: transparent;")

        self.main_frame.setStyleSheet(f"""
            #MainFrame {{ 
                background-color: {palette['main_bg']}; 
                border-radius: 24px; 
                border: 1px solid {palette['card_border']}; 
            }}

            QScrollArea, #ScrollContainer, QScrollArea > QWidget > QWidget {{
                background: transparent;
                background-color: transparent;
                border: none;
            }}

            #MainTitle {{ color: {palette['text_main']}; }}

            #ActionButton {{
                background: {palette['widget_bg']}; 
                border: 1px solid {palette['card_border']}; 
                border-radius: 12px; 
                color: {palette['text_dim']}; 
                font-size: 20px;
            }}
            #ActionButton:hover {{ 
                color: {palette['accent']}; 
                border: 1px solid {palette['accent']}; 
            }}

            #DeleteButton {{
                background: {palette['widget_bg']};
                border: 1px solid {palette['card_border']};
                border-radius: 10px;
                color: {palette['danger_text']};
                font-weight: bold;
            }}
            #DeleteButton:hover {{
                background: {palette['danger_text']};
                color: white;
            }}

            #ModernInput, #ModernCombo {{
                background: {palette['widget_bg']};
                border: 1px solid {palette['card_border']};
                border-radius: 8px;
                padding: 8px 12px;
                color: {palette['text_main']};
                font-weight: 500;
            }}

            #ModernCombo::drop-down {{ border: none; }}

            #ModernCombo QAbstractItemView {{
                background-color: {palette['widget_bg']};
                border: 1px solid {palette['card_border']};
                selection-background-color: {palette['accent']};
                color: {palette['text_main']};
                outline: none;
                border-radius: 8px;
            }}
        """)

        # 3. Force update on all child widgets and refresh style polish
        for i in range(self.s_layout.count()):
            item = self.s_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if hasattr(widget, 'update_theme'):
                    widget.update_theme(palette)
                else:
                    widget.setStyleSheet("background: transparent;")

        # FIX: Force the reset button to re-read the stylesheet
        if hasattr(self, 'reset_btn'):
            self.reset_btn.style().unpolish(self.reset_btn)
            self.reset_btn.style().polish(self.reset_btn)

    def _get_resize_edge(self, pos):
        w, h = self.width(), self.height()
        x, y = pos.x(), pos.y()
        m = self._margin
        if x < m and y < m: return Qt.TopLeftCorner
        if x > w - m and y < m: return Qt.TopRightCorner
        if x < m and y > h - m: return Qt.BottomLeftCorner
        if x > w - m and y > h - m: return Qt.BottomRightCorner
        if x < m: return Qt.LeftEdge
        if x > w - m: return Qt.RightEdge
        if y < m: return Qt.TopEdge
        if y > h - m: return Qt.BottomEdge
        return None

    def mousePressEvent(self, event):
        edge = self._get_resize_edge(event.pos())
        if edge:
            self._resize_edge = edge
        elif event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
        event.accept()

    def mouseMoveEvent(self, event):
        if not event.buttons():
            edge = self._get_resize_edge(event.pos())
            cursors = {Qt.LeftEdge: Qt.SizeHorCursor, Qt.RightEdge: Qt.SizeHorCursor,
                       Qt.TopEdge: Qt.SizeVerCursor, Qt.BottomEdge: Qt.SizeVerCursor,
                       Qt.TopLeftCorner: Qt.SizeBDiagCursor, Qt.BottomRightCorner: Qt.SizeBDiagCursor,
                       Qt.TopRightCorner: Qt.SizeFDiagCursor, Qt.BottomLeftCorner: Qt.SizeFDiagCursor}
            self.setCursor(cursors.get(edge, Qt.ArrowCursor))
        if self._resize_edge:
            self._handle_resize(event.globalPos())
        elif self._drag_pos:
            self.move(event.globalPos() - self._drag_pos)
        event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self._resize_edge = None
        self.setCursor(Qt.ArrowCursor)

    def _handle_resize(self, global_pos):
        geo = self.geometry()
        if self._resize_edge == Qt.RightEdge:
            geo.setRight(global_pos.x())
        elif self._resize_edge == Qt.LeftEdge:
            geo.setLeft(global_pos.x())
        elif self._resize_edge == Qt.BottomEdge:
            geo.setBottom(global_pos.y())
        elif self._resize_edge == Qt.TopEdge:
            geo.setTop(global_pos.y())
        elif self._resize_edge == Qt.BottomRightCorner:
            geo.setBottomRight(global_pos)
        elif self._resize_edge == Qt.TopLeftCorner:
            geo.setTopLeft(global_pos)
        if geo.width() >= 600 and geo.height() >= 500:
            self.setGeometry(geo)
