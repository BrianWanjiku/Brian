# jarvis/core/proxy_agent.py

import time
import numpy as np
from services.vision_service import VisionService
from shared.logging_utils import get_logger
from core.security import get_camera

log = get_logger("proxy_agent")

class SyntheticProxy:
    def __init__(self):
        self.vision = VisionService()
        self.focus_threshold = 0.65  # 65% attention required for interruption

    def handle_incoming_call(self, caller_id, transcript_preview):
        """
        Decision loop for incoming voice/text proxies.
        """
        # 1. Check Admin State
        status, attention = self.vision.analyze_environment(capture_frame())
        
        if status == "ADMIN" and attention > self.focus_threshold:
            # Scenario: Admin is focused. Present the Plan A/B/C immediately.
            log.info("Admin focused. Routing call to Terminal UI.")
            return "INTERRUPT_AND_DISPLAY"
        
        elif status == "ADMIN" and attention <= self.focus_threshold:
            # Scenario: Admin is present but distracted/looking away. 
            # Jarvis handles the first 30 seconds of the call silently.
            log.info("Admin distracted. Entering Proxy Mode.")
            return "SILENT_PROXY_CAPTURE"

        else:
            # Scenario: Admin not present. 
            # Jarvis acts as the Machine, recording and analyzing for threats.
            log.info(f"Admin absent. {status} detected. Recording for audit.")
            return "AUTONOMOUS_RECORDING"


def capture_frame():
    """Helper to pull current frame via system camera routers."""
    cap = get_camera()
    if cap is not None:
        ret, frame = cap.read()
        cap.release()
        if ret:
            return frame
            
    # Fallback blank frame if camera is fully locked by the Vision daemon
    return np.zeros((640, 640, 3), dtype=np.uint8)
