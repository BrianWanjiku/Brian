# jarvis/services/guardian_watchdog.py
import time
import subprocess
import cv2
import sqlite3
import sys
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Ensure jarvis root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.security import IdentityLock


class CodeIntegrityHandler(FileSystemEventHandler):
    def __init__(self):
        self.lock = IdentityLock()
        self.last_action_time = 0

    def on_modified(self, event):
        if time.time() - self.last_action_time < 3: # Enforce stricter 3s debounce
            return

        if not event.is_directory and event.src_path.endswith(".py"):
            print(f"⚠️ Code Change Detected: {event.src_path}")
            self.last_action_time = time.time() # Pre-update to prevent cascading fires on "Save All"
            self.verify_and_protect(event.src_path)

    def verify_and_protect(self, file_path):
        cap = cv2.VideoCapture(0)
        
        # MacOS camera warmup & auto-expose allowance
        for _ in range(5):
            cap.read()
            cv2.waitKey(100)
            
        cv2.waitKey(500) # Final auto-expose wait buffer for sensor brightness tuning
        ret, frame = cap.read()
        cap.release()

        if ret:
            status = self.lock.verify_presence(frame)
            if status == "ADMIN":
                print(f"✅ Admin verified. Modification permitted on {file_path}")
                # Log the change
                db_path = Path(__file__).resolve().parent.parent / "database" / "security.db"
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO audit_log (timestamp, event, detail) VALUES (datetime('now'), ?, ?)",
                    ("AUTHORIZED_MODIFICATION", f"Modified {file_path}"),
                )
                conn.commit()
                conn.close()
            else:
                print(f"🚨 UNAUTHORIZED MODIFICATION by {status}. Quarantining...")
                # Backup to quarantine instead of destroying data
                quarantine_dir = Path(__file__).resolve().parent.parent / "database" / "quarantine"
                quarantine_dir.mkdir(parents=True, exist_ok=True)
                backup_path = quarantine_dir / f"{Path(file_path).name}.{int(time.time())}.bak"
                import shutil
                shutil.move(file_path, backup_path)
                print(f"File moved to {backup_path}")
                self.alert_admin(status)

    def alert_admin(self, identity):
        from shared.config import TELEGRAM_BOT_TOKEN, ADMIN_TELEGRAM_ID
        if TELEGRAM_BOT_TOKEN:
            import asyncio
            from telegram import Bot
            async def _send():
                bot = Bot(token=TELEGRAM_BOT_TOKEN)
                await bot.send_message(chat_id=ADMIN_TELEGRAM_ID, text=f"NOTIFICATION: Intruder ({identity}) attempted to modify the core.")
            asyncio.run(_send())
        else:
            print(f"NOTIFICATION: Intruder ({identity}) attempted to modify the core.")


def start_guardian():
    path = str(Path(__file__).resolve().parent.parent) # Watch jarvis/ dir
    event_handler = CodeIntegrityHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    print(f"🛡️ Code Guardian Active. Watching {path} for unauthorized changes...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    start_guardian()
