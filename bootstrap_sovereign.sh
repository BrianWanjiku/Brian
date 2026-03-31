#!/bin/bash
# bootstrap_sovereign.sh - Sovereign v4.5 Environment Setup

echo "Initializing Sovereign v4.5 Environment..."

# 1. Install macOS system dependencies
brew install cmake dlib

# Upgrade pip and setup Python env
python3 -m pip install --upgrade pip

# 2. Install core libraries
pip install --upgrade \
    opencv-python \
    face_recognition \
    python-telegram-bot \
    aiohttp \
    watchdog \
    numpy \
    pydantic \
    pydantic-core \
    openai

# 3. Create directory tree
mkdir -p assets database logs shared

# 4. Initialize encrypted security DB (SQLite)
python3 -c "
import sqlite3
import os
conn = sqlite3.connect('database/security.db')
conn.execute('CREATE TABLE IF NOT EXISTS security_registry (id INTEGER PRIMARY KEY, name TEXT, encoding BLOB, clearance TEXT, scope TEXT)')
conn.execute('CREATE TABLE IF NOT EXISTS audit_log (timestamp TEXT, event TEXT, detail TEXT)')
conn.close()
print('✅ Security Database & Audit Table Initialized')
"

echo "Bootstrap Complete. Ready for Admin Enrollment."
