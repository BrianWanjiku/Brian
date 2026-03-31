# jarvis/core/state_manager.py
"""Working Memory — volatile runtime state + JSON persistence.

Bridges the gap between ephemeral runtime data and long-term episodic memory.
Ensures Jarvis resumes with the same 'mood' and 'focus' after a restart."""

import enum
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable
from shared.config import DB_DIR
from shared.logging_utils import get_logger

log = get_logger("state")

STATE_FILE = DB_DIR / "state.json"


class SystemState(enum.Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    EXECUTING = "executing"


class StateManager:
    """Thread-safe system state with persistent working memory (state.json)."""

    def __init__(self, state_path: Path = STATE_FILE) -> None:
        self._state = SystemState.IDLE
        self._lock = threading.Lock()
        self._callbacks: list[Callable[[SystemState, SystemState], None]] = []
        self._state_path = state_path

        # Working memory — persisted across restarts
        self.working_memory: dict = {
            "current_goal_focus": None,
            "conversation_buffer": [],
            "system_mood": "neutral",
            "current_mode": "Drafting",  # Drafting | Refining | Brainstorm
            "creative_alignment": 0,
            "last_interaction": None,
            "session_start": datetime.now().isoformat(),
        }

    # ── system state (volatile) ──────────────────────────────────────
    def get_state(self) -> SystemState:
        with self._lock:
            return self._state

    def switch_mode(self, mode: str) -> None:
        """Switch the cognitive load mode: Drafting | Refining | Brainstorm."""
        valid_modes = {"Drafting", "Refining", "Brainstorm"}
        if mode in valid_modes:
            self.working_memory["current_mode"] = mode
            log.info("Cognitive Mode switched → %s", mode)
        else:
            log.warning("Attempted to switch to invalid mode: %s", mode)

    def set_state(self, new: SystemState) -> None:
        with self._lock:
            old = self._state
            if old == new:
                return
            self._state = new
        log.info("State: %s → %s", old.value, new.value)
        for cb in self._callbacks:
            try:
                cb(old, new)
            except Exception:
                log.exception("State callback error")

    def on_transition(self, callback: Callable[[SystemState, SystemState], None]) -> None:
        self._callbacks.append(callback)

    # ── working memory (persistent) ──────────────────────────────────
    def update_mood(self, mood: str) -> None:
        self.working_memory["system_mood"] = mood
        log.info("Mood updated: %s", mood)

    def set_goal_focus(self, goal_name: str | None) -> None:
        self.working_memory["current_goal_focus"] = goal_name

    def record_interaction(self, user_input: str, response: str) -> None:
        """Append to the conversation buffer (kept small — last 10 turns)."""
        self.working_memory["last_interaction"] = datetime.now().isoformat()
        buf = self.working_memory["conversation_buffer"]
        buf.append({"user": user_input[:200], "jarvis": response[:200]})
        # Sliding window
        if len(buf) > 10:
            self.working_memory["conversation_buffer"] = buf[-10:]

    def get_state_summary(self) -> dict:
        """Return a snapshot suitable for prompt injection."""
        return {
            "system_state": self.get_state().value,
            "mood": self.working_memory["system_mood"],
            "goal_focus": self.working_memory["current_goal_focus"],
            "last_interaction": self.working_memory["last_interaction"],
        }

    # ── persistence ──────────────────────────────────────────────────
    async def save(self) -> None:
        """Serialise working memory to state.json."""
        payload = {
            "working_memory": self.working_memory,
            "saved_at": datetime.now().isoformat(),
        }
        self._state_path.write_text(json.dumps(payload, indent=2, default=str))
        log.debug("Working memory saved to %s", self._state_path)

    async def load(self) -> None:
        """Restore working memory from state.json if it exists."""
        if not self._state_path.exists():
            log.info("No state.json found — starting fresh")
            return
        try:
            data = json.loads(self._state_path.read_text())
            saved_wm = data.get("working_memory", {})
            self.working_memory.update(saved_wm)
            # Refresh session start
            self.working_memory["session_start"] = datetime.now().isoformat()
            log.info(
                "Working memory restored (mood=%s, focus=%s, saved=%s)",
                self.working_memory["system_mood"],
                self.working_memory["current_goal_focus"],
                data.get("saved_at", "unknown"),
            )
        except Exception:
            log.exception("Failed to load state.json — starting fresh")
