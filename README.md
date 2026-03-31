# Sovereign v4.5 "Ghost State"

A complete, production-ready autonomous AI node with multi-stage Ghost State hibernation, powered by OpenCV facial recognition.

## 🛡️ Core Features
- **Zero-Knowledge Security**: LLM context in `CerebellumLoop` is Fernet-encrypted and flushed from RAM instantly when Admin leaves the camera's sight.
- **Hardware Isolation**: `SensoryLoop` mic streams are physically shut down and dropped.
- **Active Deflection**: `GatewayLoop` toggles stealth mod to automatically respond to incoming Telegram/external messages with "Admin Absent".
- **OS Hard Lockdown**: `SecurityLoop` triggers cross-platform physical screen lock.

## 🚀 Quick Start (60 Seconds)
1. Add a direct, clear picture of your face to this directory named `admin_photo.jpg`.
2. Configure `.env` from the provided `.env.example`.
3. Launch via Docker:
   ```bash
   docker-compose up --build
   ```

## 🧪 Auditing Ghost State
Run the automated Pytest master auditor to cryptographically verify hibernation states, memory flushing, tamper-resistance, and audio dropping:
```bash
pytest audit_ghost_state.py -v
```
