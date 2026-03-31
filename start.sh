#!/bin/bash
# start.sh — launch Jarvis in a detached tmux session
set -euo pipefail

SESSION="jarvis"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "⚠️  Session '$SESSION' already running. Attaching..."
    tmux attach-session -t "$SESSION"
else
    echo "🚀 Starting Jarvis in tmux session: $SESSION"
    tmux new-session -d -s "$SESSION" -c "$SCRIPT_DIR" \
        "python3 run_jarvis.py; read -p 'Press enter to close...'"
    echo "✅ Jarvis is running. Attach with:  tmux attach -t $SESSION"
fi
