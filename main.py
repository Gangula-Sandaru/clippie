import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.starting_round_window import FloatingButton  # Import the new file
from db.database import create_table
from clipboard.monitor import ClipboardMonitor
import threading

if __name__ == "__main__":
    create_table()

    monitor = ClipboardMonitor()
    t = threading.Thread(target=monitor.run, daemon=True)
    t.start()

    app = QApplication(sys.argv)

    # Initialize Main Window (but don't show it yet)
    main_win = MainWindow()

    # Initialize and show the Floating Button
    floater = FloatingButton(main_win)
    floater.show()

    sys.exit(app.exec_())