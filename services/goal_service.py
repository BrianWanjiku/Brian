# jarvis/services/goal_service.py
"""Goal tracking, progress updates, and self-reflection prompt generation."""

from datetime import datetime
from shared.logging_utils import get_logger

log = get_logger("goals")


class GoalService:
    """Manages long-term goals in tasks.db and generates reflection prompts
    for the autonomous cerebellum loop."""

    def __init__(self, db) -> None:
        self.db = db
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Upgrade the goals table with extra columns if they don't exist."""
        conn = self.db._tasks_conn
        # Check existing columns
        existing = {
            row[1] for row in conn.execute("PRAGMA table_info(goals)").fetchall()
        }
        migrations = {
            "milestones": "TEXT DEFAULT ''",
            "notes": "TEXT DEFAULT ''",
            "deadline": "TEXT",
        }
        for col, typedef in migrations.items():
            if col not in existing:
                conn.execute(f"ALTER TABLE goals ADD COLUMN {col} {typedef}")
                log.info("Migrated goals table: added column '%s'", col)
        conn.commit()

    # ── CRUD ─────────────────────────────────────────────────────────
    def add_goal(self, name: str, deadline: str | None = None) -> int:
        conn = self.db._tasks_conn
        c = conn.cursor()
        c.execute(
            "INSERT INTO goals (goal_name, deadline) VALUES (?, ?)",
            (name, deadline),
        )
        conn.commit()
        log.info("Goal added: '%s' (id=%d)", name, c.lastrowid)
        return c.lastrowid

    def update_progress(
        self, goal_id: int, progress: int, notes: str = ""
    ) -> None:
        conn = self.db._tasks_conn
        conn.execute(
            "UPDATE goals SET progress=?, notes=? WHERE id=?",
            (progress, notes, goal_id),
        )
        conn.commit()
        log.info("Goal #%d progress → %d%%", goal_id, progress)

    def add_milestone(self, goal_id: int, milestone: str) -> None:
        conn = self.db._tasks_conn
        row = conn.execute(
            "SELECT milestones FROM goals WHERE id=?", (goal_id,)
        ).fetchone()
        if row is None:
            return
        existing = row[0] or ""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        updated = f"{existing}\n[{ts}] {milestone}".strip()
        conn.execute(
            "UPDATE goals SET milestones=? WHERE id=?", (updated, goal_id)
        )
        conn.commit()
        log.info("Goal #%d milestone: %s", goal_id, milestone)

    def complete_goal(self, goal_id: int) -> None:
        self.db._tasks_conn.execute(
            "UPDATE goals SET status='completed', progress=100 WHERE id=?",
            (goal_id,),
        )
        self.db._tasks_conn.commit()
        log.info("Goal #%d completed", goal_id)

    def get_active_goals(self) -> list[dict]:
        rows = self.db._tasks_conn.execute(
            "SELECT id, goal_name, progress, status, milestones, notes, deadline "
            "FROM goals WHERE status='active' ORDER BY id"
        ).fetchall()
        return [
            {
                "id": r[0],
                "goal_name": r[1],
                "progress": r[2],
                "status": r[3],
                "milestones": r[4] or "",
                "notes": r[5] or "",
                "deadline": r[6],
            }
            for r in rows
        ]

    # ── reflection ───────────────────────────────────────────────────
    def generate_reflection_prompt(self) -> str:
        """Build a self-reflection prompt from active goals for the
        autonomous cerebellum loop."""
        goals = self.get_active_goals()
        if not goals:
            return (
                "[SYSTEM REFLECTION] No active goals. "
                "Consider asking the user if there is anything they'd like to work toward."
            )

        lines = ["[SYSTEM REFLECTION] Review the following active goals and assess progress:\n"]
        for g in goals:
            lines.append(
                f"• Goal #{g['id']}: {g['goal_name']} — {g['progress']}% complete"
            )
            if g["deadline"]:
                lines.append(f"  Deadline: {g['deadline']}")
            if g["notes"]:
                lines.append(f"  Notes: {g['notes']}")
            if g["milestones"]:
                lines.append(f"  Milestones: {g['milestones']}")

        lines.append(
            "\nBased on this, decide if you should proactively suggest next steps, "
            "flag upcoming deadlines, or note any contradictions with the user's "
            "recent behaviour. Set should_interject to true only if you have "
            "something genuinely helpful to say."
        )
        return "\n".join(lines)
