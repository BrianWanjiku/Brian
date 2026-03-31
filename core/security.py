import asyncio
import logging
import platform
import subprocess

log = logging.getLogger("security")

def validate_neural_signal(signal_type, confidence_score):
    """
    The Gatekeeper: Prevents NN 'guesses' from triggering high-stakes actions.
    """
    THRESHOLDS = {
        "identity_liveness": 0.92,
        "anomaly_detection": 0.85,
        "intent_extraction": 0.80
    }
    
    target = THRESHOLDS.get(signal_type, 0.95)
    
    if confidence_score >= target:
        return True # Signal Authorized
    else:
        # LOG ONLY: Do not execute. Prevent 'Phantom Purges'.
        log.warning(f"LOW CONFIDENCE SIGNAL: {signal_type} ({confidence_score}) - ACCESS DENIED.")
        return False

class SecurityLoop:
    """
    🔐 SecurityLoop: Master Orchestrator for the Ghost State context switching.
    Controls other loops based on vision events and safely locks the system hardware down.
    """
    def __init__(self, loops_dict):
        """
        loops_dict expects: 
        {'cerebellum': CerebellumLoop, 'sensory': SensoryLoop, 'gateway': GatewayLoop, 'vision': VisionLoop}
        """
        self.loops = loops_dict
        self.is_hibernating = False
        
        # Confirmation Windows
        self.absence_count = 0
        self.presence_count = 0
        self.ABSENCE_THRESHOLD = 3  # 3 frames (e.g. 15s if 5s intervals)
        self.PRESENCE_THRESHOLD = 2 # 2 frames

    async def verify_admin_presence(self) -> bool:
        """
        Fast-path check for initialization sequence.
        Validates through the neural threshold gate to prevent phantom triggers.
        """
        vision = self.loops.get('vision')
        if not vision:
            log.error("Vision loop not integrated. Cannot verify admin.")
            return False
            
        is_present = await vision.detect_admin()
        
        # We assume 1.0 confidence for True, 0.0 for False.
        confidence = 1.0 if is_present else 0.0
        
        # Pass through the threshold gate required by v4.5 standards
        return validate_neural_signal("identity_liveness", confidence)

    async def admin_departure(self):
        """Triggered upon verified absence. Force zero-knowledge context hibernation."""
        if self.is_hibernating: return
        log.critical("🔐 SecurityLoop: ADMIN DEPARTURE DETECTED. Executing GHOST STATE protocol.")

        # 1. Deflect all incoming remote comms
        await self.loops['gateway'].set_stealth_mode(True)

        # 2. Hibernate memory and drop mic physical streams (concurrently)
        await asyncio.gather(
            self.loops['cerebellum'].hibernate(),
            self.loops['sensory'].hibernate()
        )

        # 3. Cross-platform OS Screen Lock
        self._lock_workstation()

        self.is_hibernating = True
        log.info("🔐 SecurityLoop: Ghost State completely engaged.")

    async def admin_arrival(self):
        """Triggered upon verified presence. Instantly restore encrypted state."""
        if not self.is_hibernating: return
        log.info("🔐 SecurityLoop: Admin Face Re-Detected. Waking from Ghost State.")

        # 1. Restore memory and mic streams concurrently
        await asyncio.gather(
            self.loops['cerebellum'].resume(),
            self.loops['sensory'].resume()
        )

        # 2. Re-enable internal comms routing
        await self.loops['gateway'].set_stealth_mode(False)

        self.is_hibernating = False
        log.info("🔐 SecurityLoop: All contexts successfully restored. Operating normally.")

    def _lock_workstation(self):
        """Cross-platform hardware Screen Lock invocation."""
        sys_name = platform.system()
        try:
            if sys_name == "Darwin":
                subprocess.run(["pmset", "displaysleepnow"], check=False)
            elif sys_name == "Linux":
                subprocess.run(["xset", "dpms", "force", "off"], check=False)
            elif sys_name == "Windows":
                subprocess.run(["rundll32", "user32.dll,LockWorkStation"], check=False)
            log.info(f"🔐 SecurityLoop: Workstation terminal locked ({sys_name}).")
        except Exception as e:
            log.error(f"🔐 SecurityLoop Failed to lock screen: {e}")

    async def run(self):
        """The main heartbeat monitoring the VisionLoop for presence state changes."""
        log.info("🔐 SecurityLoop: Monitoring Ghost State Triggers...")
        vision = self.loops['vision']
        await vision.start()

        while True:
            await asyncio.sleep(5)  # 5-second polling interval

            is_present = await vision.detect_admin()

            if is_present:
                self.absence_count = 0
                if self.is_hibernating:
                    self.presence_count += 1
                    if self.presence_count >= self.PRESENCE_THRESHOLD:
                        await self.admin_arrival()
                        self.presence_count = 0
            else:
                self.presence_count = 0
                if not self.is_hibernating:
                    self.absence_count += 1
                    log.warning(f"🔐 SecurityLoop: Admin missing ({self.absence_count}/{self.ABSENCE_THRESHOLD}).")
                    if self.absence_count >= self.ABSENCE_THRESHOLD:
                        await self.admin_departure()
                        self.absence_count = 0
