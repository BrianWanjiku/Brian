# jarvis/core/loop_controller.py
"""Tri-loop architecture — voice perception + reflection + state persistence."""

import asyncio
from core.state_manager import StateManager, SystemState
from core.checkpoint_manager import CheckpointManager
from services.listener_service import ListenerService
from services.scheduler_service import SchedulerService
from services.orchestrator import Orchestrator
from services.goal_service import GoalService
from services.vision_service import VisionService
from services.remote_gateway import RemoteGateway
from shared.config import HEARTBEAT_INTERVAL, REFLECTION_INTERVAL, PERSISTENCE_INTERVAL, VISION_INTERVAL
from shared.logging_utils import get_logger

log = get_logger("loop")


class JarvisCore:
    """Runs concurrent async loops (The 'God Mode' Heartbeat):
    - **Voice loop** (sensory cortex) — high-frequency perception
    - **Reflection loop** (cerebellum) — low-frequency self-awareness
    - **Persistence loop** (homeostasis) — periodic state saving & checkpoints
    - **Vision loop** (environmental) — Stagnation tracking check
    - **Remote gateway** (mesh) — Mobile connection
    """

    def __init__(
        self,
        state: StateManager,
        orchestrator: Orchestrator,
        scheduler: SchedulerService,
        listener: ListenerService,
        goal_service: GoalService,
        checkpoint: CheckpointManager,
        vision: VisionService,
        gateway: RemoteGateway,
    ) -> None:
        self.state = state
        self.orchestrator = orchestrator
        self.scheduler = scheduler
        self.listener = listener
        self.goals = goal_service
        self.checkpoint = checkpoint
        self.vision = vision
        self.gateway = gateway
        self.active = True

    # ── entry point ──────────────────────────────────────────────────
    async def start(self) -> None:
        # Restore working memory from previous session
        await self.state.load()

        log.info(
            "JarvisCore online  (voice=%.1fs, reflection=%.0fs, persist=%.0fs)",
            HEARTBEAT_INTERVAL,
            REFLECTION_INTERVAL,
            PERSISTENCE_INTERVAL,
        )
        print("\n🟢 Jarvis Cognitive OS v4 (Sovereign) online — type a command or speak.\n")

        try:
            await asyncio.gather(
                self.run_voice_loop(),
                self.run_reflection_loop(),
                self.run_persistence_loop(),
                self.run_vision_loop(),
                self.run_remote_gateway_loop(),
            )
        finally:
            # Save state on exit
            await self.state.save()
            self.checkpoint.save_snapshot()
            log.info("Final state saved on shutdown")

    # ── sensory cortex: high-frequency perception ────────────────────
    async def run_voice_loop(self) -> None:
        log.info("Voice loop started (interval=%.1fs)", HEARTBEAT_INTERVAL)
        while self.active:
            try:
                self.state.set_state(SystemState.LISTENING)
                text = await self.listener.listen()

                if text:
                    await self._handle_command(text)

                self.scheduler.check_and_execute()
                self.state.set_state(SystemState.IDLE)
                await asyncio.sleep(HEARTBEAT_INTERVAL)

            except asyncio.CancelledError:
                log.info("Voice loop cancelled")
                break
            except Exception:
                log.exception("Voice loop tick error — recovering")
                await asyncio.sleep(HEARTBEAT_INTERVAL)

        log.info("Voice loop stopped")

    # ── cerebellum: low-frequency self-reflection ────────────────────
    async def run_reflection_loop(self) -> None:
        log.info("Reflection loop started (interval=%.0fs)", REFLECTION_INTERVAL)
        await asyncio.sleep(REFLECTION_INTERVAL)

        while self.active:
            try:
                # Goal reflection
                reflection_prompt = self.goals.generate_reflection_prompt()
                log.info("Running reflection cycle")
                await self.orchestrator.route(reflection_prompt, proactive=True)

                # Daily personality anchor (consolidation)
                anchor = self.checkpoint.generate_anchor_prompt()
                if anchor:
                    log.info("Running daily personality anchor")
                    await self.orchestrator.route(anchor, proactive=True)

                await asyncio.sleep(REFLECTION_INTERVAL)

            except asyncio.CancelledError:
                log.info("Reflection loop cancelled")
                break
            except Exception:
                log.exception("Reflection loop error — recovering")
                await asyncio.sleep(REFLECTION_INTERVAL)

        log.info("Reflection loop stopped")

    # ── homeostasis: periodic state persistence ──────────────────────
    async def run_persistence_loop(self) -> None:
        log.info("Persistence loop started (interval=%.0fs)", PERSISTENCE_INTERVAL)
        while self.active:
            try:
                await asyncio.sleep(PERSISTENCE_INTERVAL)
                await self.state.save()
            except asyncio.CancelledError:
                log.info("Persistence loop cancelled")
                break
            except Exception:
                log.exception("Persistence loop error")
                await asyncio.sleep(PERSISTENCE_INTERVAL)

        log.info("Persistence loop stopped")

    # ── vision: environmental context ────────────────────────────────
    async def run_vision_loop(self) -> None:
        log.info("Vision loop started (interval=%.0fs)", VISION_INTERVAL)
        while self.active:
            try:
                assessment = await self.vision.capture_and_analyze()
                if assessment.get("assessment") == "stagnant":
                    log.info("Vision detected physical stagnation — logging for Orchestrator.")
                    # Let the system reflect on this in the next cycle:
                    self.checkpoint.memory.store_event(
                        "Physical stagnation detected. User hasn't moved.",
                        tags="telemetry"
                    )
                await asyncio.sleep(VISION_INTERVAL)
            except asyncio.CancelledError:
                log.info("Vision loop cancelled")
                break
            except Exception:
                log.exception("Vision loop error")
                await asyncio.sleep(VISION_INTERVAL)

    # ── remote gateway: mesh connection ───────────────────────────────
    async def run_remote_gateway_loop(self) -> None:
        log.info("Remote Gateway loop started")
        # Start the gateway components
        try:
            await asyncio.gather(
                self.gateway.poll_remote(),
                self.gateway.process_queue(),
            )
        except asyncio.CancelledError:
            log.info("Remote Gateway cancelled")
        except Exception:
            log.exception("Remote Gateway error")

    # ── command handling ─────────────────────────────────────────────
    async def _handle_command(self, text: str) -> None:
        text_lower = text.strip().lower()

        if text_lower in ("pause system", "shutdown", "quit", "exit"):
            log.info("Shutdown requested via command")
            self.active = False
            return

        self.state.set_state(SystemState.THINKING)
        await self.orchestrator.route(text)

    def stop(self) -> None:
        """Signal all loops to exit gracefully."""
        self.active = False
