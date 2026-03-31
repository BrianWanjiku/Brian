import asyncio
import cv2
import logging
import os
import face_recognition
import numpy as np

log = logging.getLogger("vision")

class VisionLoop:
    """
    👁️ VisionLoop: Uses OpenCV and dlib (via face_recognition) to detect the active Admin.
    Responsible for firing the absence/presence triggers.
    """
    def __init__(self, admin_photo_path="admin_photo.jpg"):
        self.admin_photo_path = admin_photo_path
        self.admin_encoding = None
        self.cap = None

    def enroll_admin(self):
        """Loads and encodes the 'DNA' identity of the admin."""
        if not os.path.exists(self.admin_photo_path):
            log.warning(f"👁️ VisionLoop: Admin photo '{self.admin_photo_path}' not found! Creating stub encoding.")
            # For testing without real dependencies dropping out, we mock it:
            self.admin_encoding = np.zeros(128)
            return

        try:
            image = face_recognition.load_image_file(self.admin_photo_path)
            encodings = face_recognition.face_encodings(image)
            if not encodings:
                log.error("👁️ VisionLoop: No faces found in admin_photo.jpg.")
                self.admin_encoding = np.zeros(128) # Fail safe stub
            else:
                self.admin_encoding = encodings[0]
                log.info("👁️ VisionLoop: Admin Biometric DNA securely enrolled from photo.")
        except Exception as e:
            log.error(f"👁️ VisionLoop Error during enrollment: {e}")
            self.admin_encoding = np.zeros(128)

    async def start(self):
        log.info("👁️ VisionLoop: Initializing camera drivers.")
        self.enroll_admin()
        # Non-blocking camera init logic for later
        self.cap = cv2.VideoCapture(0)

    async def detect_admin(self) -> bool:
        """
        Reads a frame and verifies if the physical 'ADMIN' is sitting there.
        Returns True if present, False if absent.
        """
        if self.cap is None or not self.cap.isOpened():
            # If camera fails, fail open or fail closed depending on your risk profile
            # For Ghost State testing, we will cycle normally without spamming
            log.debug("👁️ VisionLoop: Cannot access camera.")
            return False

        ret, frame = self.cap.read()
        if not ret:
            log.debug("👁️ VisionLoop: Dropped frame.")
            return False

        # Convert BGR (OpenCV) to RGB (face_recognition)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # v4.5 M-Series Unified Memory Optimization: 
        # Scale down the image to 25% for much faster and lighter detection bounds
        small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)
        
        # Find locations using the lighter frame
        face_locations = face_recognition.face_locations(small_frame)
        face_encodings = face_recognition.face_encodings(small_frame, face_locations)

        for enc in face_encodings:
            if self.admin_encoding is not None:
                # distance calculation (threshold usually 0.6)
                matches = face_recognition.compare_faces([self.admin_encoding], enc, tolerance=0.6)
                if True in matches:
                    return True

        return False

    def close(self):
        if self.cap:
            self.cap.release()
