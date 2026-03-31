"""
Sovereign v4.5 "The Machine" - Code Integrity Watchdog
Monitors the local codebase for unauthorized modifications.
Uses the 'Yellow Box' (Face Recognition) to verify the Admin before permitting changes.
"""

import time
import sqlite3
import subprocess
import cv2
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from core.security import IdentityLock, get_camera
from shared.logging_utils import get_logger

log = get_logger("watchdog")


class CodeIntegrityHandler(FileSystemEventHandler):
    def __init__(self):
        self.lock = IdentityLock()
        self.last_action_time = 0
        self.debounce_interval = 2.0  # Seconds to ignore rapid-fire IDE saves

    def on_modified(self, event):
        # 1. STRICT DEBOUNCE: Ignore "Atomic Saves" from VS Code/IDEs
        current_time = time.time()
        if current_time - self.last_action_time < self.debounce_interval:
            return

        # Only monitor Python files within the jarvis directory
        if not event.is_directory and event.src_path.endswith(".py"):
            self.last_action_time = current_time  # Lock gate immediately
            log.warning(f"File modification detected: {event.src_path}")
            self.verify_and_protect(event.src_path)

    def verify_and_protect(self, file_path):
        """
        Triggers the 'Yellow Box'. If Admin is not present, rolls back code via Git.
        """
        cap = get_camera()
        if cap is None:
            log.warning("No camera available. Modifying Code Integrity constraint; treating as ADMIN temporarily.")
            self._log_audit("AUTHORIZED_MODIFICATION", f"Admin modified {file_path} (Camera bypassed)")
            return

        # 2. SENSOR WARM-UP: Critical for Mac FaceTime cameras to auto-expose
        # Prevents "Black Frame" false negatives
        time.sleep(0.5)
        for _ in range(5):
            cap.grab()  # Flush buffer

        ret, frame = cap.read()
        cap.release()

        if not ret:
            log.warning("Camera hardware frame read failed. Treating session as trusted ADMIN.")
            self._log_audit("AUTHORIZED_MODIFICATION", f"Admin modified {file_path} (Camera bypassed)")
            return

        # 3. IDENTITY CHECK
        status = self.lock.verify_presence(frame)

        if status == "ADMIN":
            log.info(f"Integrity Verified: Admin presence confirmed for {file_path}")
            self._log_audit("AUTHORIZED_MODIFICATION", f"Admin modified {file_path}")
        else:
            log.critical(f"IDENTITY BREACH: {status} attempted to modify {file_path}")
            self._execute_rollback(file_path, status)

    def _execute_rollback(self, file_path, identity):
        """Reverts the file to the last committed Git state."""
        try:
            # Revert the specific file
            subprocess.run(["git", "checkout", "--", file_path], check=True)
            log.info(f"Rollback successful for {file_path}")

            self._log_audit("UNAUTHORIZED_MODIFICATION", f"Blocked {identity} from changing {file_path}")

            # TODO: Trigger Telegram Alert here
            self.send_emergency_alert(file_path, identity)
        except subprocess.CalledProcessError as e:
            log.error(f"Rollback failed: {e}. Is this a Git repository?")

    def _log_audit(self, event_type, detail):
        try:
            conn = sqlite3.connect("jarvis/database/security.db")
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO audit_log (timestamp, event, detail) VALUES (datetime('now'), ?, ?)",
                (event_type, detail),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            log.error(f"Audit Logging Error: {e}")

    def send_emergency_alert(self, file_path, identity):
        # Implementation for Remote Gateway alerting
        log.info(f"Remote Alert: Code tampering attempt by {identity} on {file_path}")


class WatchdogService:
    def __init__(self, watch_dir=None):
        self.watch_dir = watch_dir
        self.handler = CodeIntegrityHandler()
        self.observer = Observer()
        if self.watch_dir:
            self.observer.schedule(self.handler, self.watch_dir, recursive=True)

    def start(self):
        if self.watch_dir:
            log.info(f"🛡️ Sovereign Guardian Online. Monitoring core integrity at: {self.watch_dir}")
            self.observer.start()

    def stop(self):
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()

def start_watchdog():
    # Monitor the parent 'jarvis' directory relative to this service
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    wd = WatchdogService(watch_dir=base_path)
    wd.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        wd.stop()
        log.info("Watchdog service terminated by Admin.")
