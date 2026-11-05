#!/usr/bin/env bash
# ==============================================================================
# AI Stock Market Research & Ranking Agent (NSE & BSE)
# Launch Script for Linux / macOS / WSL
# ==============================================================================

set -e

if [ ! -f ".venv/bin/python" ]; then
    echo "[ERROR] Virtual environment not found at .venv/bin/python."
    echo "Please run './setup.sh' first to install dependencies and configure the environment."
    exit 1
fi

source .venv/bin/activate

echo "=============================================================================="
echo "  AI Stock Market Research & Ranking Agent (NSE & BSE)"
echo "  Starting Institutional FinTech Platform..."
echo "  Dashboard URL: http://127.0.0.1:8000/"
echo "  Press Ctrl + C to stop the server anytime."
echo "=============================================================================="
echo ""

python manage.py runserver 127.0.0.1:8000
