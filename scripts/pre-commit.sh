#!/usr/bin/env sh
set -eu

if ! command -v ruff >/dev/null 2>&1; then
  echo "Pre-commit failed: 'ruff' is not installed."
  echo "Install with: python -m pip install ruff"
  exit 1
fi

if ! python -c "import pytest" >/dev/null 2>&1; then
  echo "Pre-commit failed: 'pytest' is not installed."
  echo "Install with: python -m pip install pytest"
  exit 1
fi

if ! python -c "import pytest_timeout" >/dev/null 2>&1; then
  echo "Pre-commit failed: 'pytest-timeout' is not installed."
  echo "Install with: python -m pip install pytest-timeout"
  exit 1
fi

echo "Running pre-commit checks..."

echo "[1/3] Formatting check: ruff format --check ."
if ! ruff format --check .; then
  echo "Pre-commit failed: formatting check failed."
  echo "Fix: run 'ruff format .' and commit again."
  exit 1
fi

echo "[2/3] Lint check: ruff check ."
if ! ruff check .; then
  echo "Pre-commit failed: lint check failed."
  echo "Fix: run 'ruff check .' (or 'ruff check . --fix') and commit again."
  exit 1
fi

echo "[3/3] Fast tests: python -m pytest tests/ -x -q --timeout=10"
if ! python -m pytest tests/ -x -q --timeout=10; then
  echo "Pre-commit failed: fast tests failed."
  echo "Fix: run 'python -m pytest tests/ -x -q --timeout=10' and resolve failures."
  exit 1
fi

echo "Pre-commit checks passed."
