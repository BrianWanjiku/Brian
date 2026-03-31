import asyncio
import logging
from agents.cerebellum import CerebellumLoop
from services.sensory import SensoryLoop
from services.gateway import GatewayLoop
from services.vision import VisionLoop
from core.security import SecurityLoop

async def main():
    """
    Sovereign v4.5 "Ghost State" Entry Point.
    Bridges the 5 autonomous loops and waits for Admin to engage.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    log = logging.getLogger("MAIN")
    log.info("🔥 BOOTING SOVEREIGN V4.5 (Ghost State Edition) 🔥")

    # 1. Instantiate the loops
    cerebellum = CerebellumLoop()
    sensory = SensoryLoop()
    gateway = GatewayLoop()
    vision = VisionLoop(admin_photo_path="admin_photo.jpg")

    # 2. Wire Security Orchestration
    loops_dict = {
        'cerebellum': cerebellum,
        'sensory': sensory,
        'gateway': gateway,
        'vision': vision
    }
    security = SecurityLoop(loops_dict)

    # 3. Startup Phase Wait (allocate buffers, connect to mics/cameras)
    log.info("Synchronizing and warming up physical drivers...")
    await asyncio.gather(
        cerebellum.start(),
        sensory.start(),
        gateway.start()
        # Vision is started internally by SecurityLoop.run()
    )

    log.info("🛡️ ALL SYSTEMS ONLINE. AWAITING FACE DETECTION 🛡️")

    # 4. Master Orchestration Gather
    try:
        await asyncio.gather(
            security.run(),       # Heartbeat watching vision
            cerebellum.run(),     # Inference loops
            sensory.run(),        # Audio streaming
            gateway.run()         # Remote comms
        )
    except asyncio.CancelledError:
        log.warning("Graceful Shutdown Sequence Started...")
    finally:
        # Emergency cleanup if script killed
        vision.close()
        log.info("Clean exit. Goodbye.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
