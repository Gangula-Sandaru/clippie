from PyQt5.QtCore import QObject, pyqtSignal
from utils.logger import logger


class NotificationBridge(QObject):
    """
    Thread-safe signal broadcaster for application notifications.
    Can be safely called from background worker threads (like ClipboardMonitor)
    and handled on Qt's main GUI thread.
    """
    # Signal emitted when sensitive content is detected: (category, message)
    sensitive_detected = pyqtSignal(str, str)

    def emit_sensitive(self, category: str, message: str = ""):
        """
        Emit a sensitive content detection event.
        Safe to call from any thread.
        """
        try:
            self.sensitive_detected.emit(category, message)
        except Exception as e:
            logger.error("Failed to emit sensitive detection signal: %s", e, exc_info=True)


notifier = NotificationBridge()
