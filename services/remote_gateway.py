# jarvis/services/remote_gateway.py
import asyncio
from telegram import Bot
from shared.config import TELEGRAM_BOT_TOKEN, ADMIN_TELEGRAM_ID
from shared.logging_utils import get_logger

log = get_logger("gateway")

class RemoteGateway:
    def __init__(self, orchestrator) -> None:
        self.orchestrator = orchestrator
        self.token = TELEGRAM_BOT_TOKEN
        self.admin_id = int(ADMIN_TELEGRAM_ID)
        self.last_update_id = 0

    async def poll_remote(self):
        """Active polling of the Telegram API via Tailscale tunnel."""
        if not self.token: return
        
        bot = Bot(token=self.token)
        log.info("Gateway Online: Awaiting secure commands...")

        while True:
            try:
                updates = await bot.get_updates(offset=self.last_update_id + 1, timeout=10)
                for update in updates:
                    self.last_update_id = update.update_id
                    
                    # DNA LOCK: Security check for Admin ID
                    if update.message and update.message.from_user.id == self.admin_id:
                        log.info(f"Secure command received: {update.message.text}")
                        # Direct injection into the Brain
                        await self.orchestrator.route(update.message.text, proactive=False)
                    else:
                        log.warning(f"Unauthorized access attempt from: {update.effective_user.id}")
            
            except Exception as e:
                log.error(f"Gateway Error: {e}")
            
            await asyncio.sleep(1) # Prevent rate limiting
