# jarvis/services/tool_service.py
"""Secure macOS/AppleScript tool registry.

Only pre-approved AppleScript actions can be executed. The LLM cannot
run arbitrary osascript — it must pick from the registry."""

import subprocess
from shared.logging_utils import get_logger

log = get_logger("tools")

# ── Approved AppleScript registry ────────────────────────────────────
# Each entry: tool_name → { "description": ..., "script_template": ... }
# The script_template uses {param} placeholders filled from action parameters.

TOOL_REGISTRY: dict[str, dict] = {
    "set_volume": {
        "description": "Set macOS volume (0-100)",
        "script_template": 'set volume output volume {level}',
    },
    "get_volume": {
        "description": "Get current macOS volume level",
        "script_template": 'output volume of (get volume settings)',
    },
    "set_brightness": {
        "description": "Set display brightness (0.0-1.0)",
        "script_template": 'tell application "System Events" to set value of slider 1 of group 1 of group 2 of window 1 of application process "ControlCenter" to {level}',
    },
    "toggle_dnd": {
        "description": "Toggle Do Not Disturb mode",
        "script_template": (
            'tell application "System Events"\n'
            '  tell application process "ControlCenter"\n'
            '    click menu bar item "Focus" of menu bar 1\n'
            '  end tell\n'
            'end tell'
        ),
    },
    "open_app": {
        "description": "Open a macOS application by name",
        "script_template": 'tell application "{app_name}" to activate',
    },
    "quit_app": {
        "description": "Quit a macOS application by name",
        "script_template": 'tell application "{app_name}" to quit',
    },
    "clipboard_get": {
        "description": "Read the current clipboard contents",
        "script_template": 'the clipboard',
    },
    "clipboard_set": {
        "description": "Set clipboard contents",
        "script_template": 'set the clipboard to "{text}"',
    },
    "notify": {
        "description": "Display a macOS notification",
        "script_template": 'display notification "{message}" with title "Jarvis"',
    },
    "dark_mode_toggle": {
        "description": "Toggle macOS dark/light mode",
        "script_template": (
            'tell application "System Events"\n'
            '  tell appearance preferences\n'
            '    set dark mode to not dark mode\n'
            '  end tell\n'
            'end tell'
        ),
    },
}


class ToolService:
    """Executes only pre-approved AppleScript actions from the registry."""

    def __init__(self) -> None:
        log.info("Tool registry loaded: %d approved actions", len(TOOL_REGISTRY))

    def list_tools(self) -> list[dict]:
        """Return a list of available tools for prompt injection."""
        return [
            {"name": name, "description": info["description"]}
            for name, info in TOOL_REGISTRY.items()
        ]

    def list_tool_names(self) -> set[str]:
        """Return the set of registered tool names for dispatch checks."""
        return set(TOOL_REGISTRY.keys())

    def tool_descriptions_for_prompt(self) -> str:
        """Format tool list for LLM system prompt."""
        lines = []
        for name, info in TOOL_REGISTRY.items():
            lines.append(f"  • {name}: {info['description']}")
        return "\n".join(lines)

    async def confirm_and_call(self, tool_name: str, parameters: dict) -> dict:
        """Execute an approved AppleScript tool. Rejects unknown tools."""
        if tool_name not in TOOL_REGISTRY:
            log.warning("Rejected unapproved tool: %s", tool_name)
            return {
                "success": False,
                "output": f"Tool '{tool_name}' is not in the approved registry",
            }

        entry = TOOL_REGISTRY[tool_name]
        script = entry["script_template"]

        # Fill placeholders from parameters
        try:
            script = script.format(**parameters)
        except KeyError as e:
            return {
                "success": False,
                "output": f"Missing parameter for {tool_name}: {e}",
            }

        log.info("Executing AppleScript: %s", tool_name)
        return self._run_osascript(script)

    def _run_osascript(self, script: str) -> dict:
        """Execute an AppleScript via /usr/bin/osascript."""
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return {
                    "success": True,
                    "output": result.stdout.strip() or "OK",
                }
            return {
                "success": False,
                "output": result.stderr.strip() or f"Exit code {result.returncode}",
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "AppleScript timed out (10s)"}
        except Exception as exc:
            log.exception("osascript execution failed")
            return {"success": False, "output": str(exc)}
