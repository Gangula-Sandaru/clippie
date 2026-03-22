import time
from PyQt5.QtCore import QThread, pyqtSignal

class CloudSyncWorker(QThread):
    success = pyqtSignal()
    error = pyqtSignal(str)

    def run(self):
        try:
            # Simulate network latency
            time.sleep(1.5)
            # In a real scenario, we would compress the SQLite DB and upload via REST API/FTP
            self.success.emit()
        except Exception as e:
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
