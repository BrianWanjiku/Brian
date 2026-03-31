# jarvis/services/tts_service.py
"""
JARVIS TTS powered by Fish Speech 1.5 (S2-Pro model).
Gracefully degrades to macOS `say` when offline or without an API key.
"""

import os
import asyncio
import tempfile
import asyncio.subprocess
import subprocess
from fishaudio import FishAudio
from shared.logging_utils import get_logger

log = get_logger("tts")

# S2-Pro JARVIS-style voice from Fish
FISH_JARVIS_VOICE = "ef9c79b62ef34530bf452c0e50e3c260"

class TTSService:
    def __init__(self) -> None:
        api_key = os.environ.get("FISH_API_KEY")
        if api_key:
            self.client = FishAudio(api_key=api_key)
            log.info("Fish Speech 1.5 S2-Pro SDK ready (with API Key)")
        else:
            self.client = None
            log.warning("Fish Audio API key missing; TTS will use macOS 'say' only")
        self._process: asyncio.subprocess.Process | None = None

    async def speak(self, text: str, reference_id: str | None = None) -> None:
        """
        Synthesize and play speech using Fish Speech 1.5 asynchronously.
        If the FishAudio client is missing or fails, degradation to macOS say occurs.
        """
        self.stop()
        
        if self.client is not None:
            voice_id = reference_id or FISH_JARVIS_VOICE
            try:
                log.info(f"Synthesizing speech with Fish S2-Pro: {text[:80]}")
                
                # Run the synchronous SDK call in a separate thread
                # so we don't block the asyncio event loop
                audio = await asyncio.to_thread(
                    self.client.tts.convert,
                    text=text,
                    reference_id=voice_id,
                )

                # Write to a secure temp WAV file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    f.write(audio)
                    tmp_file = f.name

                try:
                    # Play on macOS
                    process = await asyncio.create_subprocess_exec(
                        "afplay", tmp_file,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    self._process = process
                    await process.wait()
                    self._process = None
                finally:
                    # Clean up temp file
                    if os.path.exists(tmp_file):
                        os.remove(tmp_file)

            except Exception as e:
                log.error(f"Fish Speech TTS failed: {e}")
                log.info("Falling back to macOS native 'say'")
                await self._fallback_speak(text)
        else:
            await self._fallback_speak(text)
            
    async def _fallback_speak(self, text: str) -> None:
        """Fallback to macOS native 'say' if Fish Speech fails or lacks key."""
        cmd = ["say", text]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._process = process
        await process.wait()
        self._process = None
        
    def stop(self) -> None:
        """Interrupt any in-progress speech (barge-in)."""
        process = self._process
        if process and process.returncode is None:
            process.terminate()
            log.info("Speech interrupted (barge-in)")
            self._process = None
