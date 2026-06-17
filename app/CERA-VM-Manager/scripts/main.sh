#!/bin/bash

# set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/../../../backend"
VENV_DIR="$BACKEND_DIR/cera-backend"

"${VENV_DIR}/bin/python3" "${BACKEND_DIR}/app/main.py" "$@" 2>&1