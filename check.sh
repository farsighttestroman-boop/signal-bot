#!/usr/bin/env bash
# Code quality + test runner for signal-bot.
# Usage: ./check.sh
# Requires: poetry (https://python-poetry.org/docs/#installation)
#           Python 3.11 available as python3.11 (used for the dev venvs)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
API="$ROOT/signal-bot-api"
UI="$ROOT/signal-bot-ui"

# If a Poetry venv is already active in the shell, poetry run respects VIRTUAL_ENV
# and ignores the project-configured venv.  Unset it so poetry picks the right one.
unset VIRTUAL_ENV 2>/dev/null || true

run() { echo "▶  $*"; "$@"; echo; }

echo "Configuring Python 3.11 venvs …"
# Pin each project to Python 3.11 (the runtime used in Docker)
poetry -C "$API" env use python3.11 -q
poetry -C "$UI"  env use python3.11 -q

echo "Installing dev dependencies …"
run poetry -C "$API" install --with dev -q
run poetry -C "$UI"  install --with dev -q

# ── Ruff (lint + format check) ───────────────────────────────────────────────
echo "════════════════════════════════════ RUFF ══"
run poetry -C "$API" run ruff check  "$API" --config "$API/pyproject.toml"
run poetry -C "$API" run ruff format --check "$API" --config "$API/pyproject.toml"
run poetry -C "$UI"  run ruff check  "$UI"  --config "$UI/pyproject.toml"
run poetry -C "$UI"  run ruff format --check "$UI"  --config "$UI/pyproject.toml"

# ── Mypy (static type checking) ───────────────────────────────────────────────
echo "════════════════════════════════════ MYPY ══"
run poetry -C "$API" run mypy \
    --config-file "$API/pyproject.toml" \
    --exclude 'tests/' \
    "$API"
run poetry -C "$UI"  run mypy \
    --config-file "$UI/pyproject.toml" \
    --exclude 'tests/' \
    "$UI"

# ── Bandit (security scan) ────────────────────────────────────────────────────
echo "══════════════════════════════════ BANDIT ══"
run poetry -C "$API" run bandit -r "$API" -c "$API/pyproject.toml" \
    --exclude "$API/tests"
run poetry -C "$UI"  run bandit -r "$UI"  -c "$UI/pyproject.toml"  \
    --exclude "$UI/tests"

# ── Pytest + coverage ─────────────────────────────────────────────────────────
echo "══════════════════════════════════ PYTEST ══"
(cd "$API" && poetry run pytest tests/ \
    --tb=short \
    --cov=. \
    --cov-report=term-missing \
    --cov-fail-under=80 \
    -v)

(cd "$UI"  && poetry run pytest tests/ \
    --tb=short \
    --cov=. \
    --cov-report=term-missing \
    --cov-fail-under=70 \
    -v)

echo "════════════════════════════════════════════"
echo "✅  All checks passed."
