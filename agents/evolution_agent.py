# jarvis/agents/evolution_agent.py
"""Self-Evolving Metacognition.
Analyzes Telemetry & Parameter Tuning based on user interaction."""

from shared.logging_utils import get_logger
from datetime import datetime

log = get_logger("evolution")


class EvolutionAgent:
    """Monitors telemetry and working memory, running a self-patch cycle."""

    def __init__(self, db) -> None:
        self.db = db

    def log_feedback(self, suggestion: str, user_response: int) -> None:
        """Log user feedback (+1 for engaged, -1 for ignored/rejected)."""
        conn = self.db._system_conn
        if conn:
            conn.execute(
                "INSERT INTO telemetry (event_type, description, value, timestamp) VALUES (?, ?, ?, ?)",
                ("feedback", suggestion, user_response, datetime.now().isoformat())
            )
            conn.commit()

    async def self_patch(self) -> str | None:
        """Run self-analysis on system parameters and return a recommendation
        if intervention is needed."""
        # Query telemetry
        conn = self.db._system_conn
        if not conn:
            return None

        # E.g., Analyze recent feedback
        rows = conn.execute(
            "SELECT value FROM telemetry WHERE event_type='feedback' ORDER BY id DESC LIMIT 10"
        ).fetchall()
        
        if not rows:
            return None

        values = [r[0] for r in rows]
        positive = sum(1 for v in values if v > 0)
        negative = sum(1 for v in values if v < 0)

        log.info("Evolution check: +%d / -%d feedback", positive, negative)

        if negative > positive and len(values) >= 5:
            # Propose tuning
            return (
                "SYSTEM EVOLUTION ALERT: I've noticed you've been dismissing or ignoring "
                "my recent proactive suggestions. Should we adjust the interruption threshold "
                "or switch my default mode to something less intrusive?"
            )
        
        return None
