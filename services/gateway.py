import asyncio
import logging

log = logging.getLogger("gateway")

class GatewayLoop:
    """
    📡 GatewayLoop: Telegram and Tailscale integration loops.
    During Ghost State, inputs are forcefully deflected gracefully.
    """
    def __init__(self):
        self.stealth_mode = False

    async def start(self):
        log.info("📡 GatewayLoop: Activating external communication hooks.")

    async def run(self):
        """Simulation of web polling or websocket keepalives."""
        log.info("📡 GatewayLoop: Listening for remote commands.")
        while True:
            await asyncio.sleep(1)
            # Pseudo polling loop could be here

    async def set_stealth_mode(self, enabled: bool):
        """Toggles the passive deflecting state from internal orchestrator commands."""
        self.stealth_mode = enabled
        if enabled:
            log.warning("📡 GatewayLoop: Stealth Mode ENABLED. All inputs will be deflected.")
        else:
            log.info("📡 GatewayLoop: Stealth Mode DISABLED. Resuming normal inputs.")

    async def handle_incoming_message(self, message: str) -> str:
        """
        Entrypoint for Telegram webhooks or manual inputs before passing to Cerebellum.
        """
        if self.stealth_mode:
            log.warning(f"📡 GatewayLoop: Deflecting message while in stealth: '{message}'")
            return "⚠️ Node in Stealth Mode. Admin presence required."
            
        # In actual prod, we pass this to the orchestrator or Cerebellum directly
        return f"📡 Received cleanly: {message}"
