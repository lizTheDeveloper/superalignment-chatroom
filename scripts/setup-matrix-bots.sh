#!/bin/bash

# Automated Matrix bot account and room setup
# Creates 10 bot accounts and 11 rooms for superalignment project

set -e  # Exit on error

HOMESERVER="https://matrix.themultiverse.school"
AGENTS=("agent-sylvia" "agent-roy" "agent-cynthia" "agent-moss" "agent-tessa" "agent-historian" "agent-architect" "agent-ray" "agent-orchestrator" "agent-monitor")
ROOMS=(
    "coordination"
    "research"
    "research-critique"
    "architecture"
    "implementation"
    "testing"
    "documentation"
    "roadmap"
    "triggers"
    "alerts"
    "status"
)

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=== Matrix Bot Setup ===${NC}"
echo "This script will create bot accounts and rooms on $HOMESERVER"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}Installing uv...${NC}"
    brew install uv
fi

# Check if matrix-commander is installed
if ! command -v matrix-commander &> /dev/null; then
    echo -e "${YELLOW}Installing matrix-commander...${NC}"
    uv tool install matrix-commander
fi

# Create output directory for credentials
CREDS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/matrix-credentials"
mkdir -p "$CREDS_DIR"

echo -e "${BLUE}=== Step 1: Creating Bot Accounts ===${NC}"
echo ""

# Prompt for password (same for all bots for simplicity)
read -sp "Enter password for all bot accounts: " BOT_PASSWORD
echo ""
echo ""

# Store tokens in associative array
declare -A TOKENS

for agent in "${AGENTS[@]}"; do
    echo -e "${YELLOW}Creating account: @${agent}:themultiverse.school${NC}"

    # Try to register via API
    REGISTER_RESPONSE=$(curl -s -X POST "${HOMESERVER}/_matrix/client/r0/register" \
        -H "Content-Type: application/json" \
        -d "{
            \"username\": \"${agent}\",
            \"password\": \"${BOT_PASSWORD}\",
            \"auth\": {\"type\": \"m.login.dummy\"}
        }")

    # Check if registration succeeded
    if echo "$REGISTER_RESPONSE" | grep -q "access_token"; then
        TOKEN=$(echo "$REGISTER_RESPONSE" | jq -r '.access_token')
        TOKENS[$agent]=$TOKEN
        echo -e "${GREEN}✓ Created @${agent}:themultiverse.school${NC}"
    else
        # Account might already exist, try to login
        echo -e "${YELLOW}  Account may exist, trying to login...${NC}"

        LOGIN_RESPONSE=$(curl -s -X POST "${HOMESERVER}/_matrix/client/r0/login" \
            -H "Content-Type: application/json" \
            -d "{
                \"type\": \"m.login.password\",
                \"user\": \"${agent}\",
                \"password\": \"${BOT_PASSWORD}\"
            }")

        if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
            TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
            TOKENS[$agent]=$TOKEN
            echo -e "${GREEN}✓ Logged in as @${agent}:themultiverse.school${NC}"
        else
            echo -e "${RED}❌ Failed to create/login ${agent}${NC}"
            echo "Response: $LOGIN_RESPONSE"
            echo ""
            echo "You may need to create this account manually or check server settings."
            exit 1
        fi
    fi

    echo ""
done

echo -e "${BLUE}=== Step 2: Creating Rooms ===${NC}"
echo ""

# Use orchestrator token to create rooms
ORCHESTRATOR_TOKEN="${TOKENS[agent-orchestrator]}"
declare -A ROOM_IDS

for room in "${ROOMS[@]}"; do
    ROOM_NAME="superalignmenttoutopia-${room}"
    echo -e "${YELLOW}Creating room: #${ROOM_NAME}${NC}"

    CREATE_RESPONSE=$(curl -s -X POST "${HOMESERVER}/_matrix/client/r0/createRoom" \
        -H "Authorization: Bearer ${ORCHESTRATOR_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"${ROOM_NAME}\",
            \"preset\": \"public_chat\",
            \"visibility\": \"public\",
            \"room_alias_name\": \"${ROOM_NAME}\"
        }")

    if echo "$CREATE_RESPONSE" | grep -q "room_id"; then
        ROOM_ID=$(echo "$CREATE_RESPONSE" | jq -r '.room_id')
        ROOM_IDS[$room]=$ROOM_ID
        echo -e "${GREEN}✓ Created room: ${ROOM_ID}${NC}"

        # Invite all bots to this room
        echo -e "${YELLOW}  Inviting all bots...${NC}"
        for agent in "${AGENTS[@]}"; do
            curl -s -X POST "${HOMESERVER}/_matrix/client/r0/rooms/${ROOM_ID}/invite" \
                -H "Authorization: Bearer ${ORCHESTRATOR_TOKEN}" \
                -H "Content-Type: application/json" \
                -d "{\"user_id\": \"@${agent}:themultiverse.school\"}" > /dev/null
        done
        echo -e "${GREEN}  ✓ All bots invited${NC}"
    else
        echo -e "${RED}❌ Failed to create room: ${ROOM_NAME}${NC}"
        echo "Response: $CREATE_RESPONSE"
    fi

    echo ""
done

echo -e "${BLUE}=== Step 3: Saving Configuration ===${NC}"
echo ""

# Save tokens to environment file
ENV_FILE="${CREDS_DIR}/.env"
echo "# Matrix Bot Tokens" > "$ENV_FILE"
echo "# Generated: $(date)" >> "$ENV_FILE"
echo "" >> "$ENV_FILE"
echo "MATRIX_HOMESERVER=\"${HOMESERVER}\"" >> "$ENV_FILE"
echo "" >> "$ENV_FILE"

for agent in "${AGENTS[@]}"; do
    # Remove "agent-" prefix for environment variable name
    AGENT_NAME=${agent#agent-}
    AGENT_UPPER=$(echo "$AGENT_NAME" | tr '[:lower:]' '[:upper:]')
    echo "MATRIX_TOKEN_${AGENT_UPPER}=\"${TOKENS[$agent]}\"" >> "$ENV_FILE"
done

echo -e "${GREEN}✓ Saved tokens to: $ENV_FILE${NC}"
echo ""

# Save room mapping to JSON
ROOMS_JSON="${CREDS_DIR}/matrix-rooms.json"
echo "{" > "$ROOMS_JSON"
first=true
for room in "${ROOMS[@]}"; do
    if [ "$first" = false ]; then
        echo "," >> "$ROOMS_JSON"
    fi
    echo -n "  \"${room}\": \"${ROOM_IDS[$room]}\"" >> "$ROOMS_JSON"
    first=false
done
echo "" >> "$ROOMS_JSON"
echo "}" >> "$ROOMS_JSON"

echo -e "${GREEN}✓ Saved room mapping to: $ROOMS_JSON${NC}"
echo ""

echo -e "${BLUE}=== Setup Complete! ===${NC}"
echo ""
echo "Next steps:"
echo "1. Copy environment variables to ~/.superalignment-env:"
echo "   cat $ENV_FILE >> ~/.superalignment-env"
echo ""
echo "2. Install matrix-mcp-server (see MATRIX_SETUP.md)"
echo ""
echo "3. Update .mcp.json to use the tokens and room mapping"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: Keep $ENV_FILE secure and never commit it to git!${NC}"
echo ""
echo "Bot accounts created:"
for agent in "${AGENTS[@]}"; do
    echo "  - @${agent}:themultiverse.school"
done
echo ""
echo "Rooms created:"
for room in "${ROOMS[@]}"; do
    echo "  - #superalignmenttoutopia-${room}:themultiverse.school"
done
