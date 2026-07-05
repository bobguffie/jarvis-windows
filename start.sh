#!/usr/bin/env bash
# JARVIS Linux - Quick Start
# Run: ./start.sh (after running setup.sh once)

set -e

if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found. Run setup.sh first."
    exit 1
fi

source venv/bin/activate
python3 main.py