import asyncio
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

try:
    from shared.config import TELEGRAM_BOT_TOKEN, TELEGRAM_ADMIN_ID  # adapt to your config
except ImportError:
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TOKEN")
    TELEGRAM_ADMIN_ID = os.environ.get("TELEGRAM_ADMIN_ID", "YOUR_ID")

log = logging.getLogger("status_dashboard")

# Color‑style for PoI‑style ASCII UI
LOG_STYLES = {
    "SOVEREIGN_ROOT": "✨",
    "security": "🔐",
    "vision": "👁",
    "gateway": "📡",
    "cerebellum": "🧠",
    "sensory": "👂",
}

DEFAULT_STYLE = "🔷"


class StatusDashboard:
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.bot: Optional[Bot] = None
        self.admin_chat_id: int = TELEGRAM_ADMIN_ID
        self.running: bool = False
        self.last_position: int = 0

    def _read_new_lines(self) -> List[str]:
        lines = []
        if not self.log_path.exists():
            return lines

        try:
            with open(self.log_path, "r") as f:
                f.seek(self.last_position)
                new_lines = f.readlines()
                self.last_position = f.tell()
                lines = new_lines
        except Exception as e:
            log.error(f"Error reading log file: {e}")

        return lines

    def _format_log_line(self, line: str) -> str:
        # Extract name from format like:
        # 2025-03-22 15:00:00 - SOVEREIGN_ROOT - INFO - INITIALIZING SOVEREIGN v4.5 BOOT SEQUENCE
        m = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (\w+) - (\w+) - (.*)", line)
        if not m:
            return f"🔷 {line.strip()}"

        timestamp, logger_name, level, message = m.groups()
        emoji = LOG_STYLES.get(logger_name, DEFAULT_STYLE)
        short_level = {
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "🔥",
            "CRITICAL": "💀"
        }.get(level, "❓")

        return f"{emoji}{short_level} {timestamp} {message}"

    async def send_log_update(self, log_lines: List[str]):
        if not self.bot or len(log_lines) == 0:
            return

        text = "\n".join(
            [self._format_log_line(line) for line in log_lines[-30:]]  # latest 30 lines
        )

        try:
            await self.bot.send_message(
                chat_id=self.admin_chat_id,
                text=f"```text\n{text}\n```",
                parse_mode="MarkdownV2",
            )
        except Exception as e:
            log.error(f"Failed to send Telegram message: {e}")

    async def _tail_log(self, interval: float = 0.5):
        while self.running:
            lines = self._read_new_lines()
            if lines:
                await self.send_log_update(lines)

            await asyncio.sleep(interval)

    async def start(self):
        self.running = True
        self.last_position = 0

        log.info("Status Dashboard starting. Tail log...")
        await self._tail_log()

    def stop(self):
        self.running = False


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dashboard = context.application.job_queue._jobs["status_dashboard"].data
    await update.message.reply_text("Status Dashboard is active. Streaming logs.")


async def cmd_force_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dashboard = context.application.job_queue._jobs["status_dashboard"].data
    lines = dashboard._read_new_lines()
    if lines:
        text = "\n".join(
            [dashboard._format_log_line(line) for line in lines[-30:]]
        )
        await update.message.reply_text(
            f"```text\n{text}\n```",
            parse_mode="MarkdownV2",
        )
    else:
        await update.message.reply_text("No new log lines detected.")


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    log_path = Path("logs/system.log")
    if not log_path.exists():
        log_path.parent.mkdir(exist_ok=True)
        log_path.write_text("")

    bot = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    dashboard = StatusDashboard(log_path)
    dashboard.bot = bot.bot  # inject bot client

    # Add handlers
    bot.add_handler(CommandHandler("status", cmd_status))
    bot.add_handler(CommandHandler("refresh", cmd_force_refresh))

    # Run the dashboard in the background when the bot starts
    async def schedule_dashboard():
        job = bot.job_queue.run_once(
            lambda ctx: asyncio.create_task(dashboard.start()),
            when=0,
            data=dashboard,
            name="status_dashboard",
        )
        return job

    # Run bot
    async with bot:
        task = asyncio.create_task(schedule_dashboard())
        await bot.start()
        await bot.updater.start_polling()
        await task

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Status Dashboard stopped.")
