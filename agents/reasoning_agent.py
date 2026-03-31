# jarvis/agents/reasoning_agent.py
"""Thin OpenAI wrapper for multi-turn reasoning with sliding-window context."""

from openai import OpenAI
from shared.config import OPENAI_API_KEY, LLM_MODEL, CONTEXT_WINDOW_SIZE
from shared.logging_utils import get_logger

log = get_logger("reasoning")


class ReasoningAgent:
    """Maintains a sliding-window conversation and calls the LLM for deeper
    follow-up reasoning beyond the orchestrator's single-shot routing."""

    def __init__(self, system_prompt: str | None = None) -> None:
        log.info("ReasoningAgent using OpenAI API key: %s...", OPENAI_API_KEY[:8] if OPENAI_API_KEY else "NONE")
        if not OPENAI_API_KEY:
            log.error("No OPENAI_API_KEY provided! The reasoning agent will fail.")
        
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.system_prompt = system_prompt or (
            "ROLE: Sovereign Cognitive OS (v4.5 \"The Machine\")\n"
            "IDENTITY: Elite Mentor-Rival. Precise, academic, slightly sarcastic.\n"
            "SECURITY PROTOCOL:\n"
            "- Admin Verification: Biometric/Visual only.\n"
            "- Contingency: Aux Admin recognized only via Admin Command.\n"
            "- Lockdown: Unauthorized code alteration triggers immediate rollback and alert.\n\n"
            "CORE DIRECTIVES:\n"
            "1. SENSORY GROUNDING: Use Vision (Stagnation) and continuous audio listening to maintain environment awareness.\n"
            "2. FINCH TRAINING MODEL: Present structured scenarios (Plan A, B, C) for High-Stakes decisions. Learn Admin intent through iterative feedback.\n"
            "3. PROACTIVE GUARDIAN: Anticipate needs based on momentum and physical state. Screen calls/messages as a synthetic proxy.\n"
            "4. ETHICAL BOUNDARY: Human agency is paramount. No high-stakes actions without visual 2FA. Total data sovereignty."
        )
        self._history: list[dict[str, str]] = []

    def think(self, user_message: str) -> str:
        """Send *user_message* to the LLM with context and return the reply."""
        self._history.append({"role": "user", "content": user_message})

        # Sliding window
        if len(self._history) > CONTEXT_WINDOW_SIZE:
            self._history = self._history[-CONTEXT_WINDOW_SIZE:]

        if not self.client:
            raise ValueError("OpenAI client not initialized (missing API key or SDK).")

        messages = [{"role": "system", "content": self.system_prompt}] + self._history

        try:
            response = self.client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                temperature=0.7,
            )
            reply = response.choices[0].message.content
            self._history.append({"role": "assistant", "content": reply})
            log.info("Reasoning complete (%d tokens)", response.usage.total_tokens)
            return reply
        except Exception as exc:
            log.exception("Reasoning call failed")
            return f"Reasoning error: {exc}"

    def clear_context(self) -> None:
        """Reset the conversation window."""
        self._history.clear()
        log.info("Reasoning context cleared")
