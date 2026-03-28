#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR=".venv"
VENV_PY="${VENV_DIR}/bin/python"
VENV_PIP="${VENV_DIR}/bin/pip"

echo "==> Room2Learn setup starting"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Error: ${PYTHON_BIN} is not installed."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "Error: npm is not installed. Install Node.js 18+ and npm first."
  exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
  echo "==> Creating virtual environment at ${VENV_DIR}"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
else
  echo "==> Using existing virtual environment at ${VENV_DIR}"
fi

if [ ! -x "$VENV_PY" ]; then
  echo "Error: virtual environment Python not found at ${VENV_PY}"
  exit 1
fi

if [ ! -x "$VENV_PIP" ]; then
  echo "==> Bootstrapping pip in virtual environment"
  "$VENV_PY" -m ensurepip --upgrade
fi

echo "==> Upgrading pip/setuptools/wheel"
"$VENV_PY" -m pip install --upgrade pip setuptools wheel

if [ -f "requirements.txt" ]; then
  echo "==> Installing Python runtime dependencies"
  "$VENV_PIP" install -r requirements.txt
fi

echo "==> Installing Python dev tools (ruff, pre-commit)"
"$VENV_PIP" install ruff pre-commit

if [ -f "package-lock.json" ]; then
  echo "==> Installing Node dependencies with npm ci"
  npm ci
elif [ -f "package.json" ]; then
  echo "==> Installing Node dependencies with npm install"
  npm install
fi

if [ -d ".git" ] && [ -f ".pre-commit-config.yaml" ]; then
  echo "==> Installing pre-commit git hook"
  "$VENV_PY" -m pre_commit install
  echo "==> Running pre-commit checks once"
  "$VENV_PY" -m pre_commit run --all-files || true
fi

echo
echo "Setup complete."
echo "Next steps:"
echo "  source .venv/bin/activate"
echo "  uvicorn app.main:app --reload --port 8000"
