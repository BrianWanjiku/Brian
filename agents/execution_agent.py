# jarvis/agents/execution_agent.py
"""Tool caller — safe, sandboxed actions with structured results."""

import json
import os
import subprocess
from shared.logging_utils import get_logger

log = get_logger("execution")

# Allowlisted shell commands (safety gate)
_ALLOWED_COMMANDS = {
    "ls", "cat", "head", "tail", "wc", "date", "uptime", "whoami",
    "df", "du", "echo", "pwd", "which", "open", "pbcopy", "pbpaste",
    "curl", "ping", "dig", "sw_vers", "system_profiler",
}


class ExecutionAgent:
    """Executes tools requested by the orchestrator. Every tool returns a
    structured dict ``{"success": bool, "output": str}``."""

    def __init__(self, db=None) -> None:
        self.db = db

    def run(self, action: str, parameters: dict) -> dict:
        """Dispatch *action* to the matching tool handler."""
        handler = {
            "run_shell": self._run_shell,
            "read_file": self._read_file,
            "write_file": self._write_file,
            "calculator": self._calculator,
            "web_search": self._web_search,
            "simulate_plans": self._simulate_plans,
            "record_rlhf_choice": self._record_rlhf_choice,
        }.get(action)

        if not handler:
            log.warning("Unknown tool: %s", action)
            return {"success": False, "output": f"Unknown tool: {action}"}

        try:
            result = handler(parameters)
            log.info("Tool %s → %s", action, str(result)[:200])
            return result
        except Exception as exc:
            log.exception("Tool %s failed", action)
            return {"success": False, "output": str(exc)}

    # ── tools ────────────────────────────────────────────────────────
    def _run_shell(self, params: dict) -> dict:
        cmd = params.get("command", "")
        import shlex
        args = shlex.split(cmd)
        binary = args[0] if args else ""
        if binary not in _ALLOWED_COMMANDS:
            return {"success": False, "output": f"Command '{binary}' is not allowlisted"}
        try:
            result = subprocess.run(
                args, shell=False, capture_output=True, text=True, timeout=15,
            )
            return {
                "success": result.returncode == 0,
                "output": (result.stdout or result.stderr)[:2000],
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "Command timed out (15s)"}
        except Exception as exc:
            return {"success": False, "output": str(exc)}

    def _read_file(self, params: dict) -> dict:
        path = params.get("path", "")
        if not os.path.isfile(path):
            return {"success": False, "output": f"File not found: {path}"}
        try:
            with open(path, "r") as f:
                content = f.read(10_000)  # cap at 10 KB
            return {"success": True, "output": content}
        except Exception as exc:
            return {"success": False, "output": str(exc)}

    def _write_file(self, params: dict) -> dict:
        path = params.get("path", "")
        content = params.get("content", "")
        if not path:
            return {"success": False, "output": "No path provided"}
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
            return {"success": True, "output": f"Written {len(content)} bytes to {path}"}
        except Exception as exc:
            return {"success": False, "output": str(exc)}

    def _calculator(self, params: dict) -> dict:
        expr = params.get("expression", "")
        try:
            # Safe eval — only allow numeric operations
            allowed = set("0123456789+-*/.() ")
            if not all(c in allowed for c in expr):
                return {"success": False, "output": "Unsafe expression format"}
            # Evaluate without builtins for safety
            result = eval(expr, {"__builtins__": None}, {})  # noqa: S307
            return {"success": True, "output": str(result)}
        except Exception as exc:
            return {"success": False, "output": str(exc)}

    def _web_search(self, params: dict) -> dict:
        query = params.get("query", "")
        # Stub — in production, integrate DuckDuckGo API or similar
        return {
            "success": True,
            "output": f"(web_search stub) Results for: {query}",
        }

    # ── Finch Training (RLHF) ────────────────────────────────────────
    def _simulate_plans(self, params: dict) -> dict:
        """Simulate 3 distinct plans (A, B, C) for high-stakes actions."""
        task = params.get("task", "")
        if not task:
            return {"success": False, "output": "No task provided for simulation."}
            
        from agents.reasoning_agent import ReasoningAgent
        system_pt = "Draft 3 distinct plans (A, B, C) for the given task. Plan A: Formal. Plan B: Pivot/Soft. Plan C: Brief/Buy-time."
        ra = ReasoningAgent(system_prompt=system_pt)
        drafts = ra.think(f"Task: {task}\nReturn ONLY the three plans formatted as:\nPlan A: ...\nPlan B: ...\nPlan C: ...")
        
        return {
            "success": True,
            "output": f"Finch Simulation complete. Options:\n{drafts}\n(Awaiting Admin choice via 'record_rlhf_choice')"
        }

    def _record_rlhf_choice(self, params: dict) -> dict:
        """Record the selected plan style to influence future weights."""
        choice = params.get("choice", "")
        task = params.get("task", "")
        if not choice or not task:
            return {"success": False, "output": "Requires 'choice' and 'task' parameters."}
            
        from datetime import datetime
        from pathlib import Path
        from shared.config import BASE_DIR
        
        try:
            conn = self.db.get_system_conn()
            if not conn:
                return {"success": False, "output": "System database connection not available"}
                
            conn.execute("CREATE TABLE IF NOT EXISTS rlhf_weights (task TEXT, chosen_plan TEXT, count INTEGER DEFAULT 0)")
            res = conn.execute("SELECT count FROM rlhf_weights WHERE task=? AND chosen_plan=?", (task, choice)).fetchone()
            if res:
                conn.execute("UPDATE rlhf_weights SET count=? WHERE task=? AND chosen_plan=?", (res[0]+1, task, choice))
            else:
                conn.execute("INSERT INTO rlhf_weights (task, chosen_plan, count) VALUES (?, ?, 1)", (task, choice, 1))
            self.db._system_conn.commit()
            
            with open(BASE_DIR / "database" / "evolution_audit.log", "a") as f:
                f.write(f"[{datetime.now().isoformat()}] RLHF Feedback: Admin selected {choice} for '{task}'. Weights updated.\n")
                
            return {"success": True, "output": f"RLHF weights updated successfully for {task} -> {choice}"}
        except Exception as e:
            return {"success": False, "output": str(e)}
