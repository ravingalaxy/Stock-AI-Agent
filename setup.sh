#!/usr/bin/env bash
# ==============================================================================
# AI Stock Market Research & Ranking Agent (NSE & BSE)
# Automated Linux / macOS / WSL Setup
# ==============================================================================

set -e

echo "=============================================================================="
echo "  AI Stock Market Research & Ranking Agent (NSE & BSE)"
echo "  Automated Linux / macOS Setup"
echo "=============================================================================="
echo ""

# 1. Verify Python Installation
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "[ERROR] Python 3 is not installed or not in your PATH."
    echo "Please install Python 3.10, 3.11, or 3.12 (e.g., sudo apt install python3 python3-venv python3-pip or brew install python)."
    exit 1
fi

PY_VER=$($PYTHON_CMD --version 2>&1)
echo "[1/6] Found $PY_VER"

# 2. Create Virtual Environment
if [ ! -d ".venv" ]; then
    echo "[2/6] Creating virtual environment in .venv..."
    $PYTHON_CMD -m venv .venv
else
    echo "[2/6] Virtual environment .venv already exists."
fi

# 3. Upgrade pip and Install Dependencies
echo "[3/6] Installing dependencies from requirements.txt..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Environment Configuration
echo "[4/6] Setting up environment configuration..."
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
    echo "      Created .env from .env.example"
fi
if [ ! -f "config/.env" ] && [ -f "config/.env.example" ]; then
    cp config/.env.example config/.env
    echo "      Created config/.env from config/.env.example"
fi

# 5. Ensure Runtime Folders Exist
mkdir -p data/reports data/logs

# 6. Run Database Migrations and Seed Universe
echo "[5/6] Applying database migrations..."
python manage.py migrate --noinput

echo "[6/6] Seeding baseline Indian equity universe & IPO data..."
python manage.py seed_universe

echo ""
echo "=============================================================================="
echo "  Setup Completed Successfully!"
echo "  To launch the application:"
echo "    - Run: ./run.sh"
echo "    - Or: source .venv/bin/activate && python manage.py runserver 127.0.0.1:8000"
echo "=============================================================================="
echo ""
