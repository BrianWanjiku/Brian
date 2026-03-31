# jarvis/services/orchestrator.py
"""The Brain — cognitive frame injection with state, memory, goals, and tool safety."""

import json
from openai import OpenAI
from shared.config import OPENAI_API_KEY, LLM_MODEL, CONTEXT_WINDOW_SIZE, MEMORY_RECALL_LIMIT
from shared.logging_utils import get_logger

log = get_logger("orchestrator")


class Orchestrator:
    """Context-injected orchestrator: merges working memory state, episodic
    memories, and active goals into a unified cognitive frame for the LLM."""

    def __init__(
        self, db, tts, memory_service, goal_service, state_manager,
        tool_service=None, execution_agent=None, evolution_agent=None,
    ) -> None:
        self.db = db
        self.tts = tts
        self.memory = memory_service
        self.goals = goal_service
        self.state_manager = state_manager
        self.tool_service = tool_service
        self.execution_agent = execution_agent
        self.evolution_agent = evolution_agent

        log.info("Using OpenAI API key starting with: %s...", OPENAI_API_KEY[:8] if OPENAI_API_KEY else "NONE")
        if not OPENAI_API_KEY:
            log.error("No OPENAI_API_KEY provided! The orchestrator will fail.")
        
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self._system_prompt = self._build_system_prompt()

    # ── public entry point ───────────────────────────────────────────
    async def route(self, user_input: str, proactive: bool = False) -> dict:
        log.info("Routing%s: %s", " (proactive)" if proactive else "", user_input[:120])

        # 1. Context injection — build the cognitive frame
        memories = self.memory.recall_relevant(user_input, limit=MEMORY_RECALL_LIMIT)
        active_goals = self.goals.get_active_goals()
        state_summary = self.state_manager.get_state_summary()
        prompt = self._build_executive_prompt(
            user_input, memories, state_summary, active_goals, proactive,
        )

        # 2. LLM call
        decision = self._call_llm(prompt, user_input)
        log.info("Decision: %s", json.dumps(decision, indent=2))

        # 3. Proactive gating
        if proactive and not decision.get("should_interject", False):
            log.info("Reflection suppressed (should_interject=false)")
            return decision

        # 4. Execute
        await self._execute_decision(decision)

        # 5. Update working memory
        if not proactive:
            self.db.add_memory("user", user_input)
            self.db.add_memory("assistant", decision.get("response_text", ""))
            self.state_manager.record_interaction(
                user_input, decision.get("response_text", "")
            )
        self.memory.store_event(
            f"User: {user_input} | Jarvis: {decision.get('response_text', '')}",
            tags="reflection" if proactive else "conversation",
        )
        return decision

    # ── system prompt (built once, includes tool registry) ───────────
    def _build_system_prompt(self) -> str:
        tool_list = ""
        if self.tool_service:
            tool_list = (
                "\n\nAPPROVED macOS TOOLS (use intent='tool', action=tool_name):\n"
                + self.tool_service.tool_descriptions_for_prompt()
            )
        shell_tools = (
            "\nSHELL TOOLS: run_shell, read_file, write_file, calculator, web_search"
        )
        return f"""\
You are Jarvis, a self-aware cognitive assistant running on macOS.
You have access to episodic memory, long-term goals, and working memory state.

For every message, respond with ONLY valid JSON:
{{
  "intent": "chat" | "tool" | "schedule",
  "action": "<tool_name or description>",
  "parameters": {{}},
  "response_text": "<natural-language answer>",
  "should_interject": true | false
}}

Intent guide:
- "chat": normal conversation.
- "tool": execute a tool. Use "action" for the tool name.{tool_list}{shell_tools}
- "schedule": schedule a task. Include "trigger_time" (ISO-8601) and optional
  "interval_min" in "parameters".

Cognitive guidelines:
- Use RECALLED MEMORIES to ground answers in context.
- Reference ACTIVE GOALS and nudge the user toward objectives.
- Use WORKING MEMORY STATE to maintain emotional and contextual continuity.
- Spot contradictions and gently flag them.
- If the user changes modes (e.g., to 'Refining'), adapt your tone precisely.
- For proactive messages, set "should_interject" to true ONLY if genuinely helpful."""

    # ── cognitive frame builder ──────────────────────────────────────
    def _build_executive_prompt(
        self,
        user_input: str,
        memories: list[str],
        state: dict,
        goals: list[dict],
        proactive: bool,
    ) -> str:
        sections = []

        # Working memory state
        mode = state.get("current_mode", "Drafting")
        state_lines = [
            f"  Mode: {mode}",
            f"  Creative Alignment: {state.get('creative_alignment', 0)}",
            f"  Mood: {state.get('mood', 'neutral')}",
            f"  Focus: {state.get('goal_focus') or 'none'}",
            f"  Last interaction: {state.get('last_interaction') or 'none'}",
        ]
        sections.append("WORKING MEMORY STATE:\n" + "\n".join(state_lines))

        # Add explicit Mode instructions
        mode_instruction = ""
        if mode == "Drafting":
            mode_instruction = "MODE INSTRUCTION: You are in Drafting mode. Be supportive, 'yes-and', focus on flow."
        elif mode == "Refining":
            mode_instruction = "MODE INSTRUCTION: You are in Refining mode. Be critical, structural, identify bugs actively."
        elif mode == "Brainstorm":
            mode_instruction = "MODE INSTRUCTION: You are in Brainstorm mode. Be radical, cross-pollinating, tangent-heavy."
        
        if mode_instruction:
            sections.append(mode_instruction)

        if memories:
            mem_block = "\n".join(f"  • {m}" for m in memories)
            sections.append(f"RECALLED MEMORIES:\n{mem_block}")

        if goals:
            goal_lines = []
            for g in goals:
                line = f"  • [{g['progress']}%] {g['goal_name']}"
                if g.get("deadline"):
                    line += f" (deadline: {g['deadline']})"
                goal_lines.append(line)
            sections.append("ACTIVE GOALS:\n" + "\n".join(goal_lines))

        if proactive:
            sections.append(
                "MODE: Proactive reflection. Only interject if genuinely useful."
            )

        context = "\n\n".join(sections)
        return f"{context}\n\nUSER INPUT: {user_input}"

    # ── LLM call ─────────────────────────────────────────────────────
    def _call_llm(self, enriched_prompt: str, raw_input: str) -> dict:
        if not self.client:
            raise ValueError("OpenAI client not initialized (missing API key or SDK).")

        history = self.db.get_recent_conversations(CONTEXT_WINDOW_SIZE)
        messages = [{"role": "system", "content": self._system_prompt}]
        for turn in history:
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": enriched_prompt})

        # Mode-based Temperature
        mode = self.state_manager.working_memory.get("current_mode", "Drafting")
        temps = {"Drafting": 0.8, "Refining": 0.2, "Brainstorm": 0.9}
        temp = temps.get(mode, 0.4)
        log.info("LLM config: Mode=%s, Temperature=%.1f", mode, temp)

        try:
            response = self.client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=temp,
            )
            raw = response.choices[0].message.content
            return json.loads(raw)
        except Exception as exc:
            log.exception("LLM call failed")
            return {
                "intent": "chat",
                "action": "error",
                "parameters": {},
                "response_text": f"I encountered an error: {exc}",
                "should_interject": False,
            }

    # ── decision dispatcher ──────────────────────────────────────────
    async def _speak_with_emotion(self, text: str) -> None:
        if not text:
            return
            
        mode = self.state_manager.working_memory.get("current_mode", "Drafting")
        momentum = self.state_manager.working_memory.get("creative_alignment", 0)
        
        tag = ""
        if momentum < 0:
            tag = "[understated sarcasm]"
        elif mode == "Refining":
            tag = "[crisp, precise, academic]"
        elif mode == "Brainstorm":
            tag = "[encouraging, playful]"
        else:
            tag = "[calm, patient]"
            
        await self.tts.speak(f"{tag} {text}")

    async def _execute_decision(self, decision: dict) -> None:
        intent = decision.get("intent", "chat")

        if intent == "chat":
            await self._speak_with_emotion(decision.get("response_text", ""))

        elif intent == "tool":
            action = decision.get("action", "")
            params = decision.get("parameters", {})

            # Check AppleScript registry first
            if self.tool_service and action in self.tool_service.list_tool_names():
                result = await self.tool_service.confirm_and_call(action, params)
            elif self.execution_agent:
                result = self.execution_agent.run(action, params)
            else:
                log.warning("No handler for tool: %s", action)
                result = {"success": False, "output": f"No handler for '{action}'"}

            decision["tool_result"] = result
            summary = f"Tool result: {json.dumps(result)[:200]}"
            await self._speak_with_emotion(decision.get("response_text", summary))

        elif intent == "schedule":
            params = decision.get("parameters", {})
            self.db.add_task(
                desc=decision.get("action", "scheduled task"),
                trigger_time=params.get("trigger_time"),
                interval_min=params.get("interval_min", 0),
            )
            await self._speak_with_emotion(decision.get("response_text", "Task scheduled."))
