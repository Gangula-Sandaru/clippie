"""
utils/updater.py - Auto-update module for Clippie.
Checks GitHub Releases API for new versions and handles download + install.
"""

import os
import sys
import threading
import tempfile
import subprocess
import urllib.request
import urllib.error
import json
from dataclasses import dataclass

from utils.logger import logger

# Single source of truth for version - imported from app_config
from app_config import APP_VERSION

GITHUB_REPO = "Gangula-Sandaru/clippie"
_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
_TIMEOUT = 8


@dataclass
class UpdateInfo:
    latest_version: str
    download_url: str
    release_notes: str


def _parse_version(v: str) -> tuple:
    v = v.lstrip("v").strip()
    try:
        return tuple(int(x) for x in v.split("."))
    except ValueError:
        return (0,)


def _is_newer(latest: str, current: str) -> bool:
    return _parse_version(latest) > _parse_version(current)


def _find_windows_asset(assets: list):
    fallback = None
    for asset in assets:
        name = asset.get("name", "").lower()
        url = asset.get("browser_download_url", "")
        if not url:
            continue
        if name == "clippie-setup.exe":
            return url
        if name.endswith(".exe"):
            fallback = url
    return fallback


def check_for_update():
    """Query GitHub Releases API. Returns UpdateInfo or None. Blocking - run in a thread."""
    try:
        req = urllib.request.Request(
            _API_URL,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "Clippie/" + APP_VERSION,
            },
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        tag = data.get("tag_name", "")
        body = data.get("body", "")
        assets = data.get("assets", [])

        if not tag:
            return None

        latest_version = tag.lstrip("v").strip()

        if not _is_newer(latest_version, APP_VERSION):
            logger.info("Updater: already on latest version (%s).", APP_VERSION)
            return None

        download_url = _find_windows_asset(assets)
        if not download_url:
            logger.warning("Updater: new version %s found but no Windows asset.", latest_version)
            return None

        logger.info("Updater: new version %s available (current: %s).", latest_version, APP_VERSION)
        return UpdateInfo(
            latest_version=latest_version,
            download_url=download_url,
            release_notes=body,
        )

    except urllib.error.URLError as e:
        logger.warning("Updater: network error checking for updates: %s", e)
        return None
    except Exception as e:
        logger.error("Updater: unexpected error: %s", e, exc_info=True)
        return None


def check_for_update_async(on_update_found, on_up_to_date=None):
    """
    Non-blocking: runs check_for_update() in a daemon thread.
    on_update_found(info) is called if a newer version exists.
    IMPORTANT: always emit a Qt signal inside on_update_found instead of
    touching widgets directly - this callback runs on a background thread.
    """
    def _worker():
        info = check_for_update()
        if info:
            on_update_found(info)
        elif on_up_to_date:
            on_up_to_date()

    t = threading.Thread(target=_worker, daemon=True, name="UpdateChecker")
    t.start()


def download_and_install(download_url, progress_callback=None, done_callback=None, error_callback=None):
    """Download the installer to a temp file and launch it. Runs in a background thread."""
    def _worker():
        try:
            tmp_path = os.path.join(tempfile.gettempdir(), "clippie-setup-update.exe")
            logger.info("Updater: downloading to %s", tmp_path)

            req = urllib.request.Request(
                download_url,
                headers={"User-Agent": "Clippie/" + APP_VERSION},
            )

            with urllib.request.urlopen(req, timeout=60) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0

                with open(tmp_path, "wb") as f:
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total > 0:
                            progress_callback(int(downloaded / total * 100))

            logger.info("Updater: download complete (%d bytes).", downloaded)

            if done_callback:
                done_callback()

            subprocess.Popen(
                [tmp_path],
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )

            import time
            time.sleep(1.5)
            from PyQt5.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.quit()

        except Exception as e:
            logger.error("Updater: download/install error: %s", e, exc_info=True)
            if error_callback:
                error_callback(str(e))

    t = threading.Thread(target=_worker, daemon=True, name="UpdateDownloader")
    t.start()
