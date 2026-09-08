import time
from PyQt5.QtCore import QThread, pyqtSignal
from utils.logger import logger

class CloudSyncWorker(QThread):
    success = pyqtSignal()
    error = pyqtSignal(str)

    def run(self):
        try:
            logger.warning("CloudSync triggered: Note that cloud sync is currently a simulated/mock feature. No remote upload is performed.")
            # Simulate network latency
            time.sleep(1.5)
            # In a real scenario, we would compress the SQLite DB and upload via authenticated REST API with TLS
            self.success.emit()
        except Exception as e:
            logger.error("CloudSync error: %s", e, exc_info=True)
            self.error.emit(str(e))

# Keep a reference to prevent garbage collection
_active_workers = []

def sync_data_to_cloud(on_success, on_error):
    """
    Mocks a cloud synchronization process in a thread.
    Takes callbacks for success and error handling to update UI.
    """
    worker = CloudSyncWorker()
    worker.success.connect(on_success)
    worker.error.connect(on_error)
    
    def cleanup():
        if worker in _active_workers:
            _active_workers.remove(worker)
            
    worker.finished.connect(cleanup)
    _active_workers.append(worker)
    worker.start()
