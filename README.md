# 🛰️ AURELIUS-V4.5-NODE

> **[INTERNAL ACCESS ONLY]** Biometrically-Gated Autonomous Intelligence Proxy.

Aurelius v4.5 is a Sovereign Node—a hardware-integrated AI system that operates on a Zero-Trust, physical-presence-first model. Unlike standard LLM wrappers, Aurelius ties the digital "mind" to the Admin's physical DNA, implementing a hard-lock on volatile RAM and system sensors during Admin absence.

## 🛠️ System Architecture (The 5-Loop Heartbeat)
| Loop | Class | Primary Protocol |
|---|---|---|
| Security | SecurityLoop | Biometric DNA-Gate & Physical Departure Logic |
| Sensory | SensoryLoop | Gated Audio (Whisper/Fish) & Mic Kill-Switch |
| Environment | EnvironmentLoop | OpenCV Motion & Stagnation Monitoring |
| Cerebellum | CerebellumLoop | Fernet-Encrypted RAM Snapshots & LLM Inference |
| Gateway | GatewayLoop | Tailscale Mesh & Telegram Tactical Mini App |

## 🔒 Hardened Security Protocols

### 1. The DNA Gatekeeper
At boot, the system executes a 5-frame retry window to verify the Admin’s facial encoding stored in `security.db`. If verification fails or lighting is below the 30-lux threshold, the system triggers an immediate `sys.exit(1)`, preventing LLM weights from loading into RAM.

### 2. "Ghost State" Hibernation
When the Admin leaves the room for >5 minutes:
 * **Physical**: macOS/Linux/Windows screen is forced to lock.
 * **Memory**: The active conversation buffer is encrypted via AES-256 (Fernet) and dumped to disk; RAM is wiped.
 * **Sensors**: The PyAudio stream is physically closed to prevent "Ghost" eavesdropping.
 * **Comms**: The Telegram Gateway enters Stealth Mode, auto-deflecting all external inquiries.

## 🚀 Installation & Deployment

### 1. Hardware Prerequisites
 * **Camera**: 720p+ for reliable biometric gating.
 * **Audio**: PyAudio-compatible microphone.
 * **Network**: Tailscale (recommended) for secure remote Tactical App access.

### 2. Dependency Injection
```bash
# Core machine learning & security libraries
pip install cryptography pyaudio opencv-python face_recognition fastapi uvicorn psutil
```

### 3. Initialization
 * **Enroll Biometrics**: Run `python enroll_admin.py` to log your DNA encoding.
 * **Configure Mesh**: Update `config.py` with your `ADMIN_TELEGRAM_ID`.
 * **Launch Node**: `python master_launcher.py`

## 📱 Tactical Command Interface
The node includes a Telegram Mini App (TMA) built for remote telemetry.
 * **URL**: `https://<YOUR_USER>.github.io/aurelius-control/`
 * **Features**: Real-time CPU/Temp monitoring, Manual Memory Purge, and Stealth Mode toggling.

## ⚖️ License & Ethics
Aurelius is a Sovereign tool. All data remains on local hardware. The system is designed to be invisible to the network and invincible to unauthorized physical access.

Node is primed.