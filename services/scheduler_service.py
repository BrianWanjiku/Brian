# jarvis/services/scheduler_service.py
"""Cron-like task runner — checks tasks.db each tick."""

from datetime import datetime
from shared.logging_utils import get_logger

log = get_logger("scheduler")


class SchedulerService:
    """Queries pending tasks, executes them, and marks them done."""

    def __init__(self, db) -> None:
        self.db = db

    def check_and_execute(self) -> list[dict]:
        """Run all tasks whose trigger_time has passed. Returns executed tasks."""
        pending = self.db.get_pending_tasks()
        executed: list[dict] = []
        for task in pending:
            log.info("Executing scheduled task #%d: %s", task["id"], task["task_desc"])
            # For now, we just mark as done. The orchestrator integration will
            # route these through the LLM for richer execution.
            self.db.complete_task(task["id"])
            executed.append(task)
        if executed:
            log.info("Scheduler executed %d task(s)", len(executed))
        return executed
