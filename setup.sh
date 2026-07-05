#!/usr/bin/env bash
# JARVIS Linux - Setup Script
# Run: chmod +x setup.sh && ./setup.sh

set -e

echo ""
echo "========================================"
echo "   J.A.R.V.I.S  Linux Setup"
echo "========================================"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "ERROR: Python3 not found. Install it: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

PYVERSION=$(python3 --version 2>&1)
echo "Python: $PYVERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# API key config
if [ ! -f "config/api_keys.json" ]; then
    if [ -f "config/api_keys.example.json" ]; then
        cp config/api_keys.example.json config/api_keys.json
        echo "Created config/api_keys.json - Add your Gemini API key there."
    fi
fi

echo ""
echo "Installing packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Make piper binary executable
if [ -f "piper/piper/piper" ]; then
    chmod +x piper/piper/piper
fi

echo ""
echo "========================================"
echo "   Setup Complete"
echo "========================================"
echo ""
echo "To start JARVIS:"
echo "   source venv/bin/activate"
echo "   python3 main.py"
echo ""
echo "Or use: ./start.sh"
echo ""