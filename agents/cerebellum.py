import asyncio
import json
import logging
import os
from cryptography.fernet import Fernet

log = logging.getLogger("cerebellum")

class CerebellumLoop:
    """
    🧠 CerebellumLoop: Manages LLM context and short-term memory buffer.
    In Ghost State, the memory buffer is zero-knowledge encrypted to disk and RAM is flushed.
    """
    def __init__(self):
        self.active_buffer: list[dict] = []
        self._encryption_key = Fernet.generate_key()
        self._fernet = Fernet(self._encryption_key)
        self.enc_file_path = "memory_snapshot.enc"
        self.is_hibernating = False

    async def start(self):
        log.info("🧠 CerebellumLoop: Initializing memory structures.")

    async def run(self):
        """Simulation of the active inference loop."""
        log.info("🧠 CerebellumLoop: Active.")
        while True:
            await asyncio.sleep(1)
            # Simulated inference could happen here if not hibernating

    async def hibernate(self):
        """
        Triggered purely on Admin departure.
        Serialize -> Encrypt -> Save to disk -> Wipe RAM buffer.
        """
        log.warning("🧠 CerebellumLoop: Hibernating. Encrypting short-term memory...")
        try:
            # Step 1: Serialize
            raw_data = json.dumps(self.active_buffer).encode('utf-8')
            
            # Step 2: Encrypt using strictly RAM-held key
            encrypted_data = self._fernet.encrypt(raw_data)
            
            # Step 3: Write payload
            with open(self.enc_file_path, 'wb') as f:
                f.write(encrypted_data)
                
            # Step 4: Flush RAM
            self.active_buffer.clear()
            self.is_hibernating = True
            log.info("🧠 CerebellumLoop: RAM flushed. Encrypted snapshot secured.")
        except Exception as e:
            log.error(f"🧠 CerebellumLoop Error during hibernation: {e}")

    async def resume(self):
        """
        Triggered when Admin securely returns.
        Decrypt -> Restore to RAM -> Delete encrypted file payload.
        """
        log.info("🧠 CerebellumLoop: Resuming. Decrypting memory snapshot...")
        if not os.path.exists(self.enc_file_path):
            log.warning("🧠 CerebellumLoop: No hibernation snapshot found.")
            self.is_hibernating = False
            return

        try:
            # Step 1: Read encrypted payload
            with open(self.enc_file_path, 'rb') as f:
                encrypted_data = f.read()
                
            # Step 2: Decrypt with RAM key
            raw_data = self._fernet.decrypt(encrypted_data)
            self.active_buffer = json.loads(raw_data.decode('utf-8'))
            
            # Step 3: Shred Payload
            os.remove(self.enc_file_path)
            self.is_hibernating = False
            log.info("🧠 CerebellumLoop: Context restored to RAM. Encrypted snapshot deleted.")
        except Exception as e:
            log.error(f"🧠 CerebellumLoop Error during resume: {e}")
            self.active_buffer = []
            self.is_hibernating = False
