#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.pefy-venv}"

"$PYTHON_BIN" -m venv "$VENV_DIR"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip
python -m pip install graphifyy
graphify --help >/dev/null

echo "Graphify bootstrap verified."
echo "For repository code analysis, prefer local AST extraction."
echo "For document/image enrichment, route through approved policy-controlled providers only."
