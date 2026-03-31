import asyncio
import aiosqlite
import time
import numpy as np
import cv2  # For Lux/Motion detection
import logging
import os

class EnvironmentLoop:
    def __init__(self, db_path="data/environmental_baseline.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.log = logging.getLogger("ENV_LOOP")

    async def _init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''CREATE TABLE IF NOT EXISTS room_logs 
                (timestamp INTEGER, motion_score FLOAT, lux_level FLOAT, audio_db FLOAT)''')
            await db.commit()

    async def get_room_metrics(self, cap, audio_stream):
        """Captures a single frame of room telemetry."""
        lux = 0.0
        peak = 0.0
        
        # 1. LUX & MOTION (Simple CV analysis)
        if cap is not None and cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                lux = np.mean(gray)  # Average brightness
        
        # 2. AUDIO LEVEL (Peak amplitude)
        if audio_stream is not None and audio_stream.is_active():
            try:
                # Read 1024 frames roughly, handle overflow exceptions
                data = np.frombuffer(audio_stream.read(1024, exception_on_overflow=False), dtype=np.int16)
                peak = np.abs(data).mean()
            except Exception as e:
                self.log.error(f"Error reading audio stream: {e}")

        return lux, peak
        
    async def check_for_anomaly(self, current_lux, current_audio):
        async with aiosqlite.connect(self.db_path) as db:
            # Get the last 24 hours of data
            async with db.execute("SELECT AVG(lux_level), AVG(audio_db) FROM room_logs") as cursor:
                row = await cursor.fetchone()
            
            if row is None or row[0] is None or row[1] is None:
                return "STABLE", 1.0
                
            avg_lux, avg_audio = row

        # Simple Statistical Anomaly: Is it 200% louder than usual?
        if avg_audio > 0 and current_audio > (avg_audio * 2.5):
            return "UNAUTHORIZED_NOISE", 0.88 # 88% Confidence
        
        return "STABLE", 1.0

    async def start(self):
        self.log.info("EnvironmentLoop: Connecting...")
        await self._init_db()

    async def run(self, cap, audio_stream):
        self.log.info("📡 TEMPORAL BASELINE LOGGING: ACTIVE")
        while True:
            lux, audio = await self.get_room_metrics(cap, audio_stream)
            
            # Log to DB every minute
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("INSERT INTO room_logs VALUES (?, ?, ?, ?)", 
                             (int(time.time()), 0.0, lux, audio))
                await db.commit()
            
            # Check for anomalies using the threshold gate framework
            status, confidence = await self.check_for_anomaly(lux, audio)
            if status != "STABLE":
                self.log.warning(f"THRESHOLD GATE WARNING: {status} ({confidence})")
                
            # Sleep for 60s to avoid DB bloat
            await asyncio.sleep(60)
