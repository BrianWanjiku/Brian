import asyncio
import logging
import pyaudio

log = logging.getLogger("sensory")

class SensoryLoop:
    """
    👂 SensoryLoop: Manages physical audio streams and microphone inputs.
    In Ghost State, it completely closes hardware streams to ensure physical hardware isolation.
    """
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.mic_enabled = False

    async def start(self):
        log.info("👂 SensoryLoop: Connecting to input streams.")
        self._open_stream()

    def _open_stream(self):
        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024
            )
            self.mic_enabled = True
        except Exception as e:
            log.error(f"👂 SensoryLoop: Failed to open audio stream: {e}")
            self.mic_enabled = False

    async def run(self):
        """Audio streaming loop."""
        log.info("👂 SensoryLoop: Active. Microphone listening.")
        while True:
            await asyncio.sleep(1)
            if self.mic_enabled and self.stream and self.stream.is_active():
                # Pseudo Audio reading chunk
                pass

    async def hibernate(self):
        """
        Hardware Isolation: Completely shut down the stream rather than just dropping frames.
        """
        log.warning("👂 SensoryLoop: Hibernating. Shutting down hardware audio streams.")
        try:
            if self.stream is not None:
                if self.stream.is_active():
                    self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            self.mic_enabled = False
            log.info("👂 SensoryLoop: Microphone physically disconnected.")
        except Exception as e:
            log.error(f"👂 SensoryLoop: Error during mic shutdown: {e}")

    async def resume(self):
        """
        Reconnect logical and hardware streams.
        """
        log.info("👂 SensoryLoop: Resuming. Re-engaging audio streams.")
        self._open_stream()
        log.info("👂 SensoryLoop: Microphone active.")
