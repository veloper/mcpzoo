#!/bin/bash
#
# MCPZoo llmcli Wrapper Script
#
# Simple wrapper to execute Python code in the MCPZoo backend environment.
#

set -euo pipefail

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to script directory
cd "${SCRIPT_DIR}"

# Ensure dependencies are installed (silent)
if [[ ! -d ".venv" ]] || [[ "pyproject.toml" -nt ".venv" ]]; then
    uv sync >/dev/null 2>&1
fi

# Unset VIRTUAL_ENV to avoid uv conflicts
unset VIRTUAL_ENV

# Set PYTHONPATH for module discovery
export PYTHONPATH="${SCRIPT_DIR}/src"

# Execute the llmcli module with all passed arguments
uv run python -m backend.llmcli "$@"
