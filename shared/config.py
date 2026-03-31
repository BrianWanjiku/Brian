# jarvis/shared/config.py
"""Central configuration — reads secrets from env, defines paths and defaults."""

import os
from pathlib import Path

# ─── Paths ───────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent          # jarvis/
DB_DIR = BASE_DIR / "database"

TASKS_DB_PATH = DB_DIR / "tasks.db"
MEMORY_DB_PATH = DB_DIR / "memory.db"

# ─── API Keys ────────────────────────────────────────────────────────
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# ─── Model Settings ──────────────────────────────────────────────────
LLM_MODEL = os.environ.get("JARVIS_LLM_MODEL", "gpt-4o-mini")
CONTEXT_WINDOW_SIZE = int(os.environ.get("JARVIS_CONTEXT_WINDOW", "20"))

# ─── TTS Settings (Fish Speech / macOS `say`) ────────────────────────
TTS_VOICE = os.environ.get("JARVIS_TTS_VOICE", "Daniel")
TTS_RATE = int(os.environ.get("JARVIS_TTS_RATE", "185"))          # words/min

FISH_SPEECH_API_URL = os.environ.get("JARVIS_FISH_SPEECH_URL", "http://localhost:8080/v1/tts")
FISH_SPEECH_REFERENCE_AUDIO = Path(os.environ.get("JARVIS_FISH_REF_AUDIO", str(BASE_DIR / "assets" / "mentor_warm.wav")))
ADMIN_FACE_PATH = Path(os.environ.get("JARVIS_ADMIN_FACE", str(BASE_DIR / "assets" / "admin_face.jpg")))
CONTINGENCY_FACE_PATH = Path(os.environ.get("JARVIS_CONTINGENCY_FACE", str(BASE_DIR / "assets" / "contingency_face.jpg")))
FISH_SPEECH_REFERENCE_TEXT = os.environ.get(
    "JARVIS_FISH_REF_TEXT", 
    "Welcome back. I have initialized the sovereign mesh and verified your administrative credentials. The local environment is stable, and the FTS5 memory banks are indexed. We have several branching scenarios to explore today—ranging from the purely theoretical to the immediately executable. I'm ready when you are, though I do suggest a quick review of yesterday's telemetry before we dive into the deep end."
)

# ─── Loop Settings ───────────────────────────────────────────────────
HEARTBEAT_INTERVAL = float(os.environ.get("JARVIS_HEARTBEAT", "2.0"))  # seconds
REFLECTION_INTERVAL = float(os.environ.get("JARVIS_REFLECTION", "600"))  # 10 min
PERSISTENCE_INTERVAL = float(os.environ.get("JARVIS_PERSIST", "30"))  # 30 sec

# ─── Memory Settings ────────────────────────────────────────────────
MEMORY_RECALL_LIMIT = int(os.environ.get("JARVIS_RECALL_LIMIT", "5"))

# ─── Checkpoint Settings ────────────────────────────────────────────
CHECKPOINT_DIR = BASE_DIR / "database" / "checkpoints"

# ─── Security / Sovereign Settings ──────────────────────────────────
ADMIN_UID = int(os.environ.get("JARVIS_ADMIN_UID", "502"))  # Typically 501 on macOS
ADMIN_TELEGRAM_ID = os.environ.get("JARVIS_ADMIN_TELEGRAM", "123456789")
TELEGRAM_BOT_TOKEN = os.environ.get("JARVIS_TELEGRAM_TOKEN", "7963538147:AAHahQ2v14N4CLJLLpWc7NTcRmCYFMHYfkQ")

# ─── Vision & Audio Settings ──────────────────────────────────────────
VISION_INTERVAL = float(os.environ.get("JARVIS_VISION_INTERVAL", "300"))  # 5 minutes
WAKE_WORD = os.environ.get("JARVIS_WAKE_WORD", "jarvis")
KILL_WORD = os.environ.get("JARVIS_KILL_WORD", "mute")

# ─── Logging ─────────────────────────────────────────────────────────
LOG_LEVEL = os.environ.get("JARVIS_LOG_LEVEL", "INFO")
