import os
import sys
import threading
from PyQt5.QtWidgets import QApplication

from app_config import config
from themes.theme_manager import theme_engine

from ui.main_window import MainWindow
from ui.starting_round_window import FloatingButton
from db.database import create_table
from clipboard.monitor import ClipboardMonitor


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)



if __name__ == "__main__":
    # Initialize Database
    create_table()

    # --- SETTINGS INITIALIZATION ---
    # Load the theme saved in config.json and apply it to the engine
    saved_theme = config.settings.get("theme", "Dark OLED")
    theme_engine.set_theme(saved_theme)

    # Note: ClipboardMonitor already imports 'config', so it will
    # use the 'history_limit' and 'startup' settings automatically.
    # --- --- --- --- --- --- --- ---

    # Start Clipboard Monitor Thread
    monitor = ClipboardMonitor()
    t = threading.Thread(target=monitor.run, daemon=True)
    t.start()

    from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
    from PyQt5.QtGui import QIcon
    from PyQt5.QtNetwork import QLocalSocket, QLocalServer

    app = QApplication(sys.argv)
    
    # --- SINGLE INSTANCE ENFORCEMENT ---
    socket = QLocalSocket()
    socket.connectToServer("ClippieSingleInstance")
    is_already_running = False
    
    if socket.waitForConnected(500):
        # We connected. Send SHOW command.
        socket.write(b"SHOW")
        socket.waitForBytesWritten(500)
        
        # Wait for the first instance to acknowledge it's alive
        if socket.waitForReadyRead(1000):
            if socket.readAll().data() == b"ACK":
                is_already_running = True
                
    if is_already_running:
        sys.exit(0)
        
    # We are the first instance (or the previous one crashed and didn't ACK)
    server = QLocalServer()
    QLocalServer.removeServer("ClippieSingleInstance")
    server.listen("ClippieSingleInstance")
    # Required for the system tray to keep running the app when all windows are closed
    app.setQuitOnLastWindowClosed(False)

    # Initialize Main Window (Styles will now be applied from the start)
    main_win = MainWindow()

    # Always instantiate so it's ready in memory, but hide unless enabled
    floater = FloatingButton(main_win)
    if config.settings.get("floating_widget", True):
        floater.show()

    if config.settings.get("first_run", True):
        from ui.onboarding_window import OnboardingWindow
        onboarding = OnboardingWindow()
        onboarding.exec_()

    # Sync startup state with registry on boot
    from utils.startup_manager import set_startup
    is_startup_enabled = config.settings.get("startup", True)
    set_startup(is_startup_enabled)

    # Open the Dashboard automatically by default on launch, unless launched on boot
    from ui.dashboard_window import HistoryWindow
    main_win.dashboard_win = None
    if "--autostart" not in sys.argv:
        main_win.dashboard_win = HistoryWindow(parent_window=main_win)
        main_win.dashboard_win.show()

    # --- SYSTEM TRAY SETUP ---
    tray = QSystemTrayIcon(QIcon(resource_path("assets/icon.ico")), app)
    
    menu = QMenu()
    # Remove system native window frame for border-radius to work on standard QMenu instances sometimes
    from PyQt5.QtCore import Qt
    menu.setWindowFlags(menu.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
    menu.setAttribute(Qt.WA_TranslucentBackground)
    
    def update_tray_theme(p):
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {p['widget_bg']};
                color: {p['text_main']};
                border: 1px solid {p['card_border']};
                border-radius: 8px;
                padding: 5px;
            }}
            QMenu::item {{
                background-color: transparent;
                padding: 6px 25px 6px 15px;
                border-radius: 5px;
                margin: 2px 4px;
                font-size: 13px;
                font-weight: 500;
            }}
            QMenu::item:selected {{
                background-color: {p['card_hover_bg']};
                color: {p['accent']};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {p['card_border']};
                margin: 4px 10px;
            }}
        """)
        
    theme_engine.theme_changed.connect(update_tray_theme)
    update_tray_theme(theme_engine.current_palette)
    
    open_action = QAction("Open Dashboard")
    def open_dash():
        if getattr(main_win, 'dashboard_win', None) is None or not main_win.dashboard_win.isVisible():
            main_win.dashboard_win = HistoryWindow(parent_window=main_win)
        main_win.dashboard_win.show()
        main_win.dashboard_win.raise_()
        main_win.dashboard_win.activateWindow()
    open_action.triggered.connect(open_dash)
    
    def on_new_connection():
        conn = server.nextPendingConnection()
        if conn.waitForReadyRead(500):
            msg = conn.readAll().data()
            if msg == b"SHOW":
                conn.write(b"ACK")
                conn.waitForBytesWritten(500)
                open_dash()
        conn.disconnectFromServer()
        
    server.newConnection.connect(on_new_connection)
    
    pause_action = QAction("Pause Tracking")
    def toggle_pause():
        monitor.is_paused = not getattr(monitor, 'is_paused', False)
        pause_action.setText("Resume Tracking" if monitor.is_paused else "Pause Tracking")
    pause_action.triggered.connect(toggle_pause)
    
    quit_action = QAction("Quit Clippie")
    quit_action.triggered.connect(app.quit)
    
    menu.addAction(open_action)
    menu.addAction(pause_action)
    menu.addSeparator()
    menu.addAction(quit_action)
    
    tray.setContextMenu(menu)
    tray.setToolTip("Clippie - Smart Clipboard Manager")
    
    def on_tray_activated(reason):
        if reason == QSystemTrayIcon.DoubleClick:
            open_dash()
            
    tray.activated.connect(on_tray_activated)
    tray.show()

    sys.exit(app.exec_())