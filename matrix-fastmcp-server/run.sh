#!/bin/bash
# Matrix FastMCP Server launcher
# Activates venv and runs the server in stdio mode

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Load environment variables
if [ -f "$HOME/.superalignment-env" ]; then
    source "$HOME/.superalignment-env"
fi

# Run the Matrix MCP server
exec python3 "$SCRIPT_DIR/src/matrix_server.py"
