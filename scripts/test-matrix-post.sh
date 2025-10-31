#!/bin/bash
# Test posting to Matrix using the FastMCP venv

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FASTMCP_DIR="$SCRIPT_DIR/../matrix-fastmcp-server"

# Activate FastMCP venv
source "$FASTMCP_DIR/venv/bin/activate"

# Load environment
if [ -f "$HOME/.superalignment-env" ]; then
    source "$HOME/.superalignment-env"
fi

# Run test script
python3 "$SCRIPT_DIR/test-post-message.py"
