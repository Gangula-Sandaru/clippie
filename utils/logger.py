"""
Centralized logging for Clippie.

Uses a RotatingFileHandler to write structured logs to:
    AppData\\Roaming\\Clippie\\clippie.log  (Windows)
    ~/.clippie/clippie.log                 (other platforms)

Intentionally does NOT import from app_config to avoid circular imports.
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler


def _get_log_path() -> str:
    """Resolve the log file path without importing app_config."""
    if sys.platform == "win32":
        base = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "Clippie")
    else:
        base = os.path.expanduser("~/.clippie")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "clippie.log")


def _build_logger() -> logging.Logger:
    log = logging.getLogger("clippie")
    log.setLevel(logging.DEBUG)

    if not log.handlers:
        handler = RotatingFileHandler(
            _get_log_path(),
            maxBytes=1_000_000,   # 1 MB per file
            backupCount=3,
            encoding="utf-8",
        )
        fmt = logging.Formatter(
            "%(asctime)s [%(levelname)-8s] %(module)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(fmt)
        log.addHandler(handler)

    return log


logger = _build_logger()
