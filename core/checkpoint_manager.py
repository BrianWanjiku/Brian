# jarvis/core/checkpoint_manager.py
"""Long-term potentiation — periodic state snapshots and daily narrative
consolidation ('Personality Anchor')."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from shared.logging_utils import get_logger

log = get_logger("checkpoint")


class CheckpointManager:
    """Creates timestamped snapshots of working memory and periodically
    consolidates raw episodic logs into narrative summaries."""

    def __init__(self, checkpoint_dir: Path, state_manager, memory_service) -> None:
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.state_manager = state_manager
        self.memory = memory_service
        self._last_anchor: str | None = None

    # ── snapshots ────────────────────────────────────────────────────
    def save_snapshot(self) -> Path:
        """Write a timestamped JSON snapshot of the current working memory."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        snap_path = self.checkpoint_dir / f"snapshot_{ts}.json"
        payload = {
            "timestamp": datetime.now().isoformat(),
            "working_memory": self.state_manager.working_memory,
            "system_state": self.state_manager.get_state().value,
            "memory_count": self.memory.count(),
        }
        snap_path.write_text(json.dumps(payload, indent=2, default=str))
        log.info("Snapshot saved: %s", snap_path.name)
        return snap_path

    def list_snapshots(self) -> list[Path]:
        return sorted(self.checkpoint_dir.glob("snapshot_*.json"), reverse=True)

    def restore_latest(self) -> dict | None:
        """Load the most recent snapshot (for disaster recovery)."""
        snaps = self.list_snapshots()
        if not snaps:
            return None
        data = json.loads(snaps[0].read_text())
        log.info("Restored snapshot: %s", snaps[0].name)
        return data

    # ── daily personality anchor ─────────────────────────────────────
    def generate_anchor_prompt(self) -> str:
        """Build a consolidation prompt that compresses a day's worth of
        episodic memories into a single narrative insight."""
        today = datetime.now().strftime("%Y-%m-%d")
        if self._last_anchor == today:
            return ""  # Already ran today

        self._last_anchor = today
        return (
            "[SYSTEM CONSOLIDATION] It is the end of the day. "
            "Review the conversation and reflection logs from today. "
            "Produce a SINGLE paragraph summarising the user's key activities, "
            "emotional tone, and any progress toward their goals. "
            "This summary becomes a permanent memory. "
            "Set should_interject to false — this is internal bookkeeping."
        )

    # ── cleanup ──────────────────────────────────────────────────────
    def prune_old_snapshots(self, keep: int = 30) -> int:
        """Keep only the most recent *keep* snapshots."""
        snaps = self.list_snapshots()
        pruned = 0
        for old in snaps[keep:]:
            old.unlink()
            pruned += 1
        if pruned:
            log.info("Pruned %d old snapshots (kept %d)", pruned, keep)
        return pruned
