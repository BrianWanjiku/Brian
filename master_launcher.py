from dotenv import load_dotenv
load_dotenv()
import asyncio
import logging
import threading
import uvicorn
import sys
from pathlib import Path

# --- 1. IMPORT YOUR NEW GATEWAY ---
import gateway_api 

from core.security import SecurityLoop
from services.sensory import SensoryLoop
from services.environment import EnvironmentLoop
from agents.cerebellum import CerebellumLoop
from services.gateway import GatewayLoop
from services.vision import VisionLoop

# --- 2. THE API THREAD WRAPPER ---
def start_api_server():
    """Runs the Tailscale-accessible API in a background thread."""
    # Binding to 0.0.0.0 is what allows your iPhone to see the Mac
    uvicorn.run(gateway_api.app, host="0.0.0.0", port=8000, log_level="error")

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    log = logging.getLogger("SOVEREIGN_ROOT")

    log.info("--- INITIALIZING SOVEREIGN v4.5 BOOT SEQUENCE ---")

    # Initialize core operational loops
    vision = VisionLoop()
    sensory = SensoryLoop()
    environment = EnvironmentLoop()
    cerebellum = CerebellumLoop()
    gateway = GatewayLoop()

    loops_dict = {
        'vision': vision,
        'sensory': sensory,
        'cerebellum': cerebellum,
        'gateway': gateway
    }

    # SECURITY (The "Gatekeeper")
    security = SecurityLoop(loops_dict)
    
    # Fast, 100% reliable rule-based check
    await vision.start()
    if not await security.verify_admin_presence():
        log.critical("ADMIN IDENTITY NOT VERIFIED. SYSTEM LOCKDOWN ENGAGED.")
        security._lock_workstation()
        sys.exit(1)
    
    log.info("✅ ADMIN IDENTITY VERIFIED. UNLOCKING CORE MESH.")

    # --- 3. THE HANDSHAKE: INJECT LIVE OBJECTS INTO THE API ---
    # This is where the placeholders are replaced with your actual running loops
    gateway_api.security = security
    gateway_api.sensory = sensory
    gateway_api.cerebellum = cerebellum
    log.info("📡 TACTICAL GATEWAY HANDSHAKE COMPLETE.")

    # --- 4. START THE REMOTE ACCESS THREAD ---
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()
    log.info("🌐 API SERVER LIVE AT http://eatmorevegetables.tailb7c548.ts.net:8000")

    # Setup phase
    log.info("Synchronizing Loop Buffers...")
    await asyncio.gather(
        sensory.start(),
        environment.start(),
        cerebellum.start(),
        gateway.start()
    )

    log.info("--- ALL LOOPS ACTIVE: AURELIUS IS ONLINE ---")

    # The "Heartbeat" - Keep all loops alive in parallel
    try:
        await asyncio.gather(
            security.run(), 
            sensory.run(),                  
            environment.run(vision.cap, sensory.stream),              
            cerebellum.run(),               
            gateway.run(),                  
        )
    except asyncio.CancelledError:
        log.warning("System Shutdown Signal Received.")
    except Exception as e:
        log.error(f"CRITICAL SYSTEM ERROR: {e}")
    finally:
        log.info("Saving system state and hibernating...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass