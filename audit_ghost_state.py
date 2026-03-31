import pytest
import asyncio
import os
import json
from agents.cerebellum import CerebellumLoop
from services.sensory import SensoryLoop
from services.gateway import GatewayLoop
from services.vision import VisionLoop
from core.security import SecurityLoop

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.mark.asyncio
async def test_ghost_state_encryption_cycle():
    """
    1. Populates test buffer
    2. Executes departure (Encrypt to disk + flush RAM)
    3. Verifies zero footprint
    4. Executes arrival (Decrypt to RAM + shred disk)
    5. Verifies perfect restore
    """
    cerebellum = CerebellumLoop()
    test_context = [{"role": "user", "content": "Hello Sovereign."}]
    cerebellum.active_buffer = list(test_context)
    
    # Assert initial start
    assert len(cerebellum.active_buffer) == 1
    
    # 1. HIBERNATE
    await cerebellum.hibernate()
    
    # 2. Verify Zero-Footprint
    assert len(cerebellum.active_buffer) == 0
    assert cerebellum.is_hibernating is True
    assert os.path.exists(cerebellum.enc_file_path)
    
    # Check that disk is genuinely encrypted and not plaintext JSON
    with open(cerebellum.enc_file_path, 'rb') as f:
        content = f.read()
        assert b"Hello Sovereign." not in content  # Plaintext shouldn't be there
        
    # 3. RESUME
    await cerebellum.resume()
    
    # 4. Verify Perfect Restoration
    assert len(cerebellum.active_buffer) == 1
    assert cerebellum.active_buffer[0]["content"] == "Hello Sovereign."
    assert not os.path.exists(cerebellum.enc_file_path)
    assert cerebellum.is_hibernating is False

@pytest.mark.asyncio
async def test_ghost_state_tamper_resistance():
    """
    Verifies that tampering with the encrypted memory file securely wipes the buffer
    instead of crashing or injecting bad context.
    """
    cerebellum = CerebellumLoop()
    cerebellum.active_buffer = [{"role": "system", "content": "SECURE DATA"}]
    await cerebellum.hibernate()
    
    # Tamper with the file (flip a byte)
    with open(cerebellum.enc_file_path, 'r+b') as f:
        f.seek(5)
        f.write(b'\x00')
        
    await cerebellum.resume()
    
    # Buffer should be wiped due to cryptography Fernet InvalidToken error
    assert len(cerebellum.active_buffer) == 0
    assert not os.path.exists(cerebellum.enc_file_path) # Should still clean up

@pytest.mark.asyncio
async def test_sensory_hardware_isolation():
    """
    Verifies PyAudio stream drops and revives on sleep wake.
    """
    sensory = SensoryLoop()
    # Mocking pyaudio might be required locally, but we'll test the flags
    await sensory.start()
    assert sensory.mic_enabled is True
    
    await sensory.hibernate()
    assert sensory.mic_enabled is False
    assert sensory.stream is None
    
    await sensory.resume()
    assert sensory.mic_enabled is True

@pytest.mark.asyncio
async def test_gateway_deflection():
    """
    Ensures message deflection triggers securely.
    """
    gateway = GatewayLoop()
    reply = await gateway.handle_incoming_message("Secret command")
    assert "cleanly" in reply
    
    await gateway.set_stealth_mode(True)
    stealth_reply = await gateway.handle_incoming_message("Secret command")
    assert "Stealth Mode. Admin presence required" in stealth_reply
