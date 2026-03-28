#!/usr/bin/env bash
set -e

PYTHON=${PYTHON:-python3}

echo "==> Checking Python..."
if ! command -v "$PYTHON" &>/dev/null; then
  echo "ERROR: Python not found. Install Python 3.10+ and try again."
  exit 1
fi

echo "==> Checking Node.js..."
if ! command -v node &>/dev/null; then
  echo "ERROR: Node.js not found. Install Node.js 18+ and try again."
  exit 1
fi

echo "==> Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
  "$PYTHON" -m venv .venv
fi

echo "==> Installing Python dependencies..."
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet flask
pip install -r requirements.txt

echo "==> Installing Node dependencies..."
npm install --silent

echo ""
echo "Done! To start the servers, open two terminals:"
echo ""
echo "  Terminal 1 (Flask backend):"
echo "    source .venv/bin/activate && python app.py"
echo ""
echo "  Terminal 2 (Vite frontend):"
echo "    npm run dev"
echo ""
echo "  Then open: https://localhost:5173"
echo "  (Accept the self-signed certificate warning — required for WebXR)"
