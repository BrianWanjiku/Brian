#!/usr/bin/env python3
# jarvis/run_jarvis.py
"""Entry point — wires all components and starts the async event loop."""

import asyncio
import signal
import sys

# Ensure the jarvis package root is on sys.path
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from shared.logging_utils import get_logger
from shared.config import (
    OPENAI_API_KEY, LLM_MODEL, TTS_VOICE,
    REFLECTION_INTERVAL, PERSISTENCE_INTERVAL, VISION_INTERVAL, CHECKPOINT_DIR,
)
from database.manager import DatabaseManager
from core.security import verify_admin_sovereignty
from core.state_manager import StateManager
from core.loop_controller import JarvisCore
from core.checkpoint_manager import CheckpointManager
from services.tts_service import TTSService
from services.listener_service import ListenerService
from services.scheduler_service import SchedulerService
from services.memory_service import MemoryService
from services.goal_service import GoalService
from services.tool_service import ToolService
from services.vision_service import VisionService
from services.remote_gateway import RemoteGateway
from services.orchestrator import Orchestrator
from services.watchdog_service import WatchdogService
from agents.execution_agent import ExecutionAgent
from agents.reasoning_agent import ReasoningAgent
from agents.evolution_agent import EvolutionAgent

log = get_logger("main")

BANNER = r"""
     ╔═══════════════════════════════════════════╗
     ║     J.A.R.V.I.S  v4.0.0  —  Sovereign     ║
     ║   Just A Rather Very Intelligent System   ║
     ║   God Mode Heartbeat · DNA Locked         ║
     ╚═══════════════════════════════════════════╝
"""


def main() -> None:
    print(BANNER)

    # ── 0. Sovereign DNA Lock ────────────────────────────────────────
    try:
        verify_admin_sovereignty()
    except PermissionError as e:
        log.error(str(e))
        sys.exit(1)

    # ── 1. Initialise databases ──────────────────────────────────────
    db = DatabaseManager()
    db.init_all()

    # ── 2. Build cognitive services ──────────────────────────────────
    state = StateManager()
    tts = TTSService()
    listener = ListenerService()
    execution = ExecutionAgent(db=db)
    reasoning = ReasoningAgent()  # noqa: F841
    evolution = EvolutionAgent(db=db)

    memory = MemoryService(db.get_memory_conn())
    goals = GoalService(db)
    tools = ToolService()
    checkpoint = CheckpointManager(CHECKPOINT_DIR, state, memory)
    vision = VisionService()

    scheduler = SchedulerService(db)
    orchestrator = Orchestrator(
        db=db,
        tts=tts,
        memory_service=memory,
        goal_service=goals,
        state_manager=state,
        tool_service=tools,
        execution_agent=execution,
        evolution_agent=evolution,
    )
    
    gateway = RemoteGateway(orchestrator=orchestrator)
    
    # Init Watchdog
    jarvis_dir = str(Path(__file__).resolve().parent)
    watchdog = WatchdogService(watch_dir=jarvis_dir)
    watchdog.start()

    # ── 3. Build the tri-loop core ───────────────────────────────────
    core = JarvisCore(
        state=state,
        orchestrator=orchestrator,
        scheduler=scheduler,
        listener=listener,
        goal_service=goals,
        checkpoint=checkpoint,
        vision=vision,
        gateway=gateway,
    )

    # ── 4. Graceful shutdown on SIGINT / SIGTERM ─────────────────────
    def _shutdown(sig, frame):
        log.info("Signal %s received — shutting down", sig)
        watchdog.stop()
        core.stop()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # ── 5. Status summary ────────────────────────────────────────────
    api_status = "✅ Connected" if OPENAI_API_KEY else "⚠️  Not set (echo mode)"
    log.info("OpenAI API key: %s", api_status)
    log.info("LLM model: %s", LLM_MODEL)
    log.info("TTS voice: %s", TTS_VOICE)
    log.info("Reflection: %.0fs  |  Persistence: %.0fs", REFLECTION_INTERVAL, PERSISTENCE_INTERVAL)
    log.info("FTS5 memories: %d  |  Approved tools: %d", memory.count(), len(tools.list_tools()))
    log.info("Checkpoints: %s", CHECKPOINT_DIR)

    # ── 6. Run ───────────────────────────────────────────────────────
    try:
        asyncio.run(core.start())
    finally:
        db.close()
        log.info("Jarvis offline. Goodbye.")


if __name__ == "__main__":
    main()
