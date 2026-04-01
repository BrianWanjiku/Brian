# AURELIUS v4.5: The Sovereign Node

An elite, production-grade autonomous AI system featuring **Ghost State** hibernation and **Neural Mission Control**. Built for absolute hardware isolation and tactical oversight via a Tailscale-secured PWA.

## 🛡️ Core Intelligence Protocols
* **Neural Mission Control (PWA)**: A custom-built, glassmorphism dashboard (v4.5) hosted on GitHub Pages. It provides real-time telemetry and command execution over a private Tailscale Mesh.
* **Zero-Knowledge "Ghost State"**: LLM context in `CerebellumLoop` is Fernet-encrypted and flushed from RAM the millisecond the `Admin` leaves the camera's FOV.
* **IdentityLock (Biometric Handshake)**: Powered by OpenCV/Dlib. Automatically toggles **Admin: ✅** status across the entire mesh based on continuous facial liveness detection.
* **Aux Admin Contingency**: Recognizes secondary authorized users (Aux Admins) via camera-log when the Primary Admin is distressed or absent. Only the Admin and logged Contingency can alter core system code.
* **Sovereign Deflection**: The `GatewayLoop` enters "Stealth Mode" when Admin is absent, obfuscating node activity and auto-responding to external pings.
* **Hardware Killswitch**: `SensoryLoop` physically drops mic streams and vision buffers during hibernation to ensure zero-leakage.

## 🚀 Deployment (3-Step Ignition)
1.  **Identity Seeding**: 
    * Place a clear photo of your face in the root directory as `admin_photo.jpg`.
    * (Optional) Add secondary authorized faces to the `/contingency` folder for Aux Admin recognition.
2.  **Network Tunneling**: Ensure **Tailscale** is active on both the Host (Mac) and the Remote (iPhone). Configure your `.env` with your Tailscale API key and Node MagicDNS.
3.  **Launch Node**:
    ```bash
    # Start the backend API and Neural Loops
    uvicorn master_launcher:app --host 0.0.0.0 --port 8000
    ```

## 📱 Dashboard Access
The control interface is a Progressive Web App (PWA). 
1.  Navigate to your GitHub Pages URL on Safari.
2.  Tap **Share** > **Add to Home Screen**.
3.  Launch **AURELIUS** from your home screen for a fullscreen, bezel-less tactical experience with custom Night Fury iconography.

## 🧪 System Auditing
Verify cryptographic memory flushing, audio dropping, and latency-induced confidence thresholds using the master auditor:
```bash
pytest audit_ghost_state.py -v --node-url http://eatmorevegetables.tailb7c548.ts.net:8000
```

---

### 🔧 Engineering Update Log (v4.5)
* **Deprecated**: Telegram Bot API (Replaced by direct Tailscale FastAPI conduit).
* **Added**: Three.js Neural Visualization for real-time inference monitoring.
* **Added**: Aux Admin "Finch-Style" training and recognition logic.
* **Added**: CORS Middleware integration for secure GitHub-to-Tailnet handshakes.
* **Fixed**: iOS PWA "Standalone" mode for zero-UI immersion.

---

### 💡 Implementation Note
The **Aux Admin** logic is handled within the `IdentityLock` loop. If the camera detects a face in the `/contingency` folder while the Primary Admin is not present, the system elevates them to `AUX_ADMIN` status, allowing system monitoring but restricting core code alterations as per protocol.
