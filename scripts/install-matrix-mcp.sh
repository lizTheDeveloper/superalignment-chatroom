#!/bin/bash

# Install and configure matrix-mcp-server for Claude Code
# Uses credentials from setup-matrix-bots.sh

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=== Installing matrix-mcp-server ===${NC}"
echo ""

# Get script directory and repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CREDS_DIR="$REPO_DIR/matrix-credentials"

# Check if credentials exist
if [ ! -f "$CREDS_DIR/.env" ]; then
    echo -e "${RED}❌ Matrix credentials not found!${NC}"
    echo ""
    echo "Please run setup-matrix-bots.sh first:"
    echo "  bash $SCRIPT_DIR/setup-matrix-bots.sh"
    exit 1
fi

# Clone matrix-mcp-server
MCP_DIR="$HOME/src/matrix-mcp-server"

if [ -d "$MCP_DIR" ]; then
    echo -e "${YELLOW}matrix-mcp-server already exists, pulling latest...${NC}"
    cd "$MCP_DIR"
    git pull
else
    echo -e "${YELLOW}Cloning matrix-mcp-server...${NC}"
    cd "$HOME/src"
    git clone https://github.com/mjknowles/matrix-mcp-server.git
    cd "$MCP_DIR"
fi

# Install dependencies and build
echo -e "${YELLOW}Installing dependencies...${NC}"
npm install

echo -e "${YELLOW}Building...${NC}"
npm run build

echo -e "${GREEN}✓ matrix-mcp-server installed${NC}"
echo ""

# Check if main repo exists
MAIN_REPO="$HOME/src/superalignmenttoutopia"
if [ ! -d "$MAIN_REPO" ]; then
    echo -e "${YELLOW}⚠️  Main repo not found at $MAIN_REPO${NC}"
    echo "Skipping .mcp.json update"
    exit 0
fi

# Load environment variables
source "$CREDS_DIR/.env"

# Update .mcp.json in main repo
MCP_CONFIG="$MAIN_REPO/.mcp.json"

echo -e "${YELLOW}Updating $MCP_CONFIG...${NC}"

# Backup existing config
if [ -f "$MCP_CONFIG" ]; then
    cp "$MCP_CONFIG" "$MCP_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
    echo -e "${GREEN}✓ Backed up existing .mcp.json${NC}"
fi

# Read existing config or create new one
if [ -f "$MCP_CONFIG" ]; then
    EXISTING_CONFIG=$(cat "$MCP_CONFIG")
else
    EXISTING_CONFIG='{
  "mcpServers": {}
}'
fi

# Add matrix-mcp-server configuration
cat > "$MCP_CONFIG" <<EOF
{
  "mcpServers": {
    "matrix-chatroom": {
      "command": "node",
      "args": [
        "$MCP_DIR/build/index.js"
      ],
      "env": {
        "MATRIX_HOMESERVER": "$MATRIX_HOMESERVER",
        "MATRIX_ACCESS_TOKEN": "\${MATRIX_TOKEN_ORCHESTRATOR}",
        "MATRIX_ROOMS_CONFIG": "$CREDS_DIR/matrix-rooms.json"
      }
    },
    "chatroom": {
      "command": "python",
      "args": [
        "-m",
        "mcp_chatroom_server"
      ],
      "cwd": "$REPO_DIR"
    }
  }
}
EOF

echo -e "${GREEN}✓ Updated .mcp.json${NC}"
echo ""

# Update ~/.superalignment-env
ENV_FILE="$HOME/.superalignment-env"

echo -e "${YELLOW}Updating $ENV_FILE...${NC}"

if [ -f "$ENV_FILE" ]; then
    # Remove old Matrix tokens if they exist
    grep -v "MATRIX_" "$ENV_FILE" > "${ENV_FILE}.tmp" || true
    mv "${ENV_FILE}.tmp" "$ENV_FILE"
fi

# Append new tokens
cat "$CREDS_DIR/.env" >> "$ENV_FILE"

echo -e "${GREEN}✓ Updated $ENV_FILE${NC}"
echo ""

echo -e "${BLUE}=== Installation Complete! ===${NC}"
echo ""
echo "Configuration:"
echo "  matrix-mcp-server: $MCP_DIR"
echo "  Credentials: $CREDS_DIR"
echo "  MCP config: $MCP_CONFIG"
echo "  Environment: $ENV_FILE"
echo ""
echo "Next steps:"
echo "1. Source the environment file:"
echo "   source $ENV_FILE"
echo ""
echo "2. Restart Claude Code to load the new MCP server"
echo ""
echo "3. Test the Matrix integration:"
echo "   - Send a message from your phone via Element app"
echo "   - Use MCP tools in Claude Code to post to rooms"
echo ""
echo -e "${YELLOW}⚠️  Remember to add $CREDS_DIR to .gitignore!${NC}"
