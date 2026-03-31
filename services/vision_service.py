# jarvis/services/vision_service.py
import asyncio
import cv2
import numpy as np
from datetime import datetime
from shared.logging_utils import get_logger
from core.security import SecurityLoop, get_camera

log = get_logger("vision")

class VisionService:
    def __init__(self, interval_sec: int = 300) -> None:
        self.interval = interval_sec
        self.last_movement = datetime.now()
        self.avg_frame = None  # Background model for motion detection
        self.cap = None

    def _init_camera(self):
        """Initializes the background camera stream with graceful degradation."""
        self.cap = get_camera()
        if not self.cap:
            log.warning("Vision Service failing gracefully: No camera available.")

    def analyze_environment(self, frame):
        # Stub attention fallback since we reverted InsightFace
        # We always return "ADMIN" and 1.0 attention to allow the Proxy to route to UI.
        return "ADMIN", 1.0

    async def run(self):
        """The heartbeat background loop."""
        self._init_camera()
        
        while True:
            await asyncio.sleep(self.interval)
            log.info("Vision service checking for movement...")
            
            if not self.cap or not self.cap.isOpened():
                self._init_camera()
                if not self.cap:
                    continue  # Wait for next interval if no camera
            
            # Clear buffer and read frame
            for _ in range(5):
                self.cap.read()
            ret, frame = self.cap.read()
            
            if not ret:
                continue

            # Convert to grayscale and blur to remove high-frequency noise
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            # Initialize background model
            if self.avg_frame is None:
                self.avg_frame = gray.astype("float")
                continue

            # Accumulate the running average
            cv2.accumulateWeighted(gray, self.avg_frame, 0.5)
            
            # Compute difference between current frame and background
            frame_delta = cv2.absdiff(gray, cv2.convertScaleAbs(self.avg_frame))
            thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
            
            # Dilate the thresholded image to fill in holes, then find contours
            thresh = cv2.dilate(thresh, None, iterations=2)
            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            significant_movement = False
            for c in contours:
                if cv2.contourArea(c) > 5000:  # Threshold for "human-sized" movement
                    significant_movement = True
                    break
            
            if significant_movement:
                log.info("Significant physical movement detected in the room.")
                self.last_movement = datetime.now()
