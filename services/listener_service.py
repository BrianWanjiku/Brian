# jarvis/services/listener_service.py
"""Non-blocking speech-to-text with stdin fallback.

If the `speech_recognition` package is installed, the microphone is used.
Otherwise the listener falls back to polling stdin so the system can run
headless or without audio hardware.
"""

import asyncio
import sys
import select
from shared.logging_utils import get_logger

log = get_logger("listener")

# Attempt optional microphone support
try:
    import speech_recognition as sr  # type: ignore[import-untyped]
    _HAS_SR = True
except ImportError:
    _HAS_SR = False


class ListenerService:
    """Provides non-blocking `listen()` that returns recognised text or None."""

    def __init__(self) -> None:
        self._recogniser = None
        self._mic = None
        if _HAS_SR:
            self._recogniser = sr.Recognizer()
            self._mic = sr.Microphone()
            log.info("Microphone listener active (speech_recognition)")
        else:
            log.info("Microphone unavailable — using stdin text fallback")

    async def listen(self) -> str | None:
        """Non-blocking listen."""
        text = await self._listen_mic() if (_HAS_SR and self._recogniser and self._mic) else await self._listen_stdin()
        return text

    # ── microphone path ──────────────────────────────────────────────
    async def _listen_mic(self) -> str | None:
        def _capture() -> str | None:
            try:
                with self._mic as source:
                    self._recogniser.adjust_for_ambient_noise(source, duration=0.3)
                    audio = self._recogniser.listen(source, timeout=3, phrase_time_limit=10)
                return self._recogniser.recognize_google(audio)
            except Exception:
                return None

        return await asyncio.to_thread(_capture)

    # ── stdin fallback ───────────────────────────────────────────────
    async def _listen_stdin(self) -> str | None:
        """Poll stdin without blocking the event loop."""
        def _poll() -> str | None:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                line = sys.stdin.readline().strip()
                return line if line else None
            return None

        return await asyncio.to_thread(_poll)
