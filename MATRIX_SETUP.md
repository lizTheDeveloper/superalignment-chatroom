# Matrix Integration Setup

Complete guide for setting up Matrix bot accounts and rooms for agent coordination.

## Prerequisites

- Access to Matrix server: `matrix.themultiverse.school`
- Admin account (or ability to create new users)
- matrix-commander CLI tool (optional but helpful)

## Step 1: Create Bot Accounts

You need to create Matrix accounts for each agent. There are two methods:

### Method A: Web Interface (Easiest)

1. Go to `https://matrix.themultiverse.school` (or use Element app)
2. Create new account for each agent:
   - Username: `sylvia`, `roy`, `cynthia`, `moss`, `tessa`, `historian`, `architect`, `ray`, `orchestrator`, `monitor`
   - Password: Use strong passwords (store in password manager)
3. Log in to each account once to activate it
4. Get access token for each account:
   - Element Web → Settings → Help & About → Advanced → Access Token
   - Copy and save to `~/.superalignment-env`

### Method B: matrix-commander CLI

```bash
# Install matrix-commander
pip install matrix-commander

# Create each bot account
matrix-commander --homeserver https://matrix.themultiverse.school \
                  --user-login sylvia \
                  --password "STRONG_PASSWORD" \
                  --device "sylvia-bot" \
                  --room-create "superalignmenttoutopia-coordination"

# Repeat for each agent
```

## Step 2: Get Access Tokens

For each bot account, you need an access token:

### Option A: Element Web

1. Log into account at https://matrix.themultiverse.school
2. Settings → Help & About → Advanced → Access Token
3. Click "Show" and copy the token (format: `syt_...`)

### Option B: matrix-commander

```bash
# Login and get token
matrix-commander --homeserver https://matrix.themultiverse.school \
                  --user-login sylvia \
                  --password "PASSWORD" \
                  --login password

# Token will be saved to ~/.config/matrix-commander/credentials.json
cat ~/.config/matrix-commander/credentials.json | grep access_token
```

### Option C: Manual API Call

```bash
# Get access token via Matrix API
curl -X POST https://matrix.themultiverse.school/_matrix/client/r0/login \
  -H "Content-Type: application/json" \
  -d '{
    "type": "m.login.password",
    "user": "sylvia",
    "password": "YOUR_PASSWORD"
  }'

# Response contains: "access_token": "syt_..."
```

## Step 3: Save Tokens to Environment

Create `~/.superalignment-env`:

```bash
# Matrix Server Configuration
export MATRIX_HOMESERVER="https://matrix.themultiverse.school"

# Bot Account Tokens
export MATRIX_TOKEN_SYLVIA="syt_c3lsdmlh_xxxxxxxxxx"
export MATRIX_TOKEN_ROY="syt_cm95_xxxxxxxxxxxxxx"
export MATRIX_TOKEN_CYNTHIA="syt_Y3ludGhpYQ_xxxxxxxx"
export MATRIX_TOKEN_MOSS="syt_bW9zcw_xxxxxxxxxxxxx"
export MATRIX_TOKEN_TESSA="syt_dGVzc2E_xxxxxxxxxxxx"
export MATRIX_TOKEN_HISTORIAN="syt_aGlzdG9yaWFu_xxxxxx"
export MATRIX_TOKEN_ARCHITECT="syt_YXJjaGl0ZWN0_xxxxxx"
export MATRIX_TOKEN_RAY="syt_cmF5_xxxxxxxxxxxxxxxx"
export MATRIX_TOKEN_ORCHESTRATOR="syt_b3JjaGVzdHJhdG9y_xx"
export MATRIX_TOKEN_MONITOR="syt_bW9uaXRvcg_xxxxxxxxx"
```

**Important:** Add to `.gitignore`! Never commit tokens.

Then source it:
```bash
# Add to ~/.bashrc or ~/.zshrc
source ~/.superalignment-env

# Or manually load for current session
source ~/.superalignment-env
```

## Step 4: Create Matrix Rooms

Create rooms with the `superalignmenttoutopia-` prefix:

### Option A: Element Web (Manual)

1. Log in as any bot account (or your admin account)
2. Create room → Set name:
   - `superalignmenttoutopia-coordination`
   - `superalignmenttoutopia-research`
   - `superalignmenttoutopia-research-critique`
   - `superalignmenttoutopia-architecture`
   - `superalignmenttoutopia-implementation`
   - `superalignmenttoutopia-testing`
   - `superalignmenttoutopia-documentation`
   - `superalignmenttoutopia-roadmap`
   - `superalignmenttoutopia-triggers`
   - `superalignmenttoutopia-alerts`
   - `superalignmenttoutopia-status`
3. Invite all bot accounts to each room
4. Set room to "Public" (or "Private" if preferred)
5. Copy room IDs (Settings → Advanced → Room ID: `!abc123:themultiverse.school`)

### Option B: matrix-commander (Automated)

```bash
# Create script to automate room creation
cat > create-rooms.sh << 'EOF'
#!/bin/bash

ROOMS=(
  "superalignmenttoutopia-coordination"
  "superalignmenttoutopia-research"
  "superalignmenttoutopia-research-critique"
  "superalignmenttoutopia-architecture"
  "superalignmenttoutopia-implementation"
  "superalignmenttoutopia-testing"
  "superalignmenttoutopia-documentation"
  "superalignmenttoutopia-roadmap"
  "superalignmenttoutopia-triggers"
  "superalignmenttoutopia-alerts"
  "superalignmenttoutopia-status"
)

for room in "${ROOMS[@]}"; do
  echo "Creating room: #$room"
  matrix-commander --room-create "$room" --room-join "$room"
done
EOF

chmod +x create-rooms.sh
./create-rooms.sh
```

### Option C: API Calls

```bash
# Create room via Matrix API
curl -X POST https://matrix.themultiverse.school/_matrix/client/r0/createRoom \
  -H "Authorization: Bearer $MATRIX_TOKEN_ORCHESTRATOR" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "superalignmenttoutopia-coordination",
    "preset": "public_chat",
    "visibility": "public"
  }'
```

## Step 5: Get Room IDs

You need to map room names to room IDs for the MCP server:

```bash
# Using matrix-commander
matrix-commander --room-list

# Or via Element Web
# Room Settings → Advanced → Room ID
```

Create a room mapping file `~/src/superalignment-chatroom/matrix-rooms.json`:

```json
{
  "coordination": "!abc123:themultiverse.school",
  "research": "!def456:themultiverse.school",
  "research-critique": "!ghi789:themultiverse.school",
  "architecture": "!jkl012:themultiverse.school",
  "implementation": "!mno345:themultiverse.school",
  "testing": "!pqr678:themultiverse.school",
  "documentation": "!stu901:themultiverse.school",
  "roadmap": "!vwx234:themultiverse.school",
  "triggers": "!yza567:themultiverse.school",
  "alerts": "!bcd890:themultiverse.school",
  "status": "!efg123:themultiverse.school"
}
```

## Step 6: Configure matrix-mcp-server

Install and configure the Matrix MCP server:

```bash
# Install matrix-mcp-server (pinned version)
cd ~/src
git clone https://github.com/mjknowles/matrix-mcp-server.git
cd matrix-mcp-server
git checkout v1.0.0  # Pin to specific version (adjust as needed)

npm install
npm run build
```

Add to `.mcp.json` in main repo:

```json
{
  "mcpServers": {
    "matrix-chatroom": {
      "command": "node",
      "args": [
        "/Users/annhoward/src/matrix-mcp-server/build/index.js"
      ],
      "env": {
        "MATRIX_HOMESERVER": "https://matrix.themultiverse.school",
        "MATRIX_ACCESS_TOKEN": "${MATRIX_TOKEN_ORCHESTRATOR}",
        "MATRIX_ROOMS_CONFIG": "/Users/annhoward/src/superalignment-chatroom/matrix-rooms.json"
      }
    },
    "chatroom": {
      "command": "/Users/annhoward/src/superalignmenttoutopia/.venv/bin/python",
      "args": [
        "/Users/annhoward/src/superalignment-chatroom/scripts/matrix-chatroom-server.py"
      ]
    }
  }
}
```

## Step 7: Test Setup

```bash
# Test bot can connect
# Using matrix-commander with saved credentials
matrix-commander --user-login orchestrator --send "Test message" --room "superalignmenttoutopia-coordination"

# Or test MCP server
# Run Claude Code and try:
# mcp__matrix-chatroom__send_message(...)
```

## Account Summary

After setup, you should have:

**Bot Accounts:**
- `@sylvia:themultiverse.school`
- `@roy:themultiverse.school`
- `@cynthia:themultiverse.school`
- `@moss:themultiverse.school`
- `@tessa:themultiverse.school`
- `@historian:themultiverse.school`
- `@architect:themultiverse.school`
- `@ray:themultiverse.school`
- `@orchestrator:themultiverse.school`
- `@monitor:themultiverse.school`

**Rooms:**
- `#superalignmenttoutopia-coordination:themultiverse.school`
- `#superalignmenttoutopia-research:themultiverse.school`
- `#superalignmenttoutopia-research-critique:themultiverse.school`
- `#superalignmenttoutopia-architecture:themultiverse.school`
- `#superalignmenttoutopia-implementation:themultiverse.school`
- `#superalignmenttoutopia-testing:themultiverse.school`
- `#superalignmenttoutopia-documentation:themultiverse.school`
- `#superalignmenttoutopia-roadmap:themultiverse.school`
- `#superalignmenttoutopia-triggers:themultiverse.school`
- `#superalignmenttoutopia-alerts:themultiverse.school`
- `#superalignmenttoutopia-status:themultiverse.school`

## Security Notes

- **Never commit access tokens** to git
- Store tokens in `~/.superalignment-env` (add to `.gitignore`)
- Use strong passwords for bot accounts
- Consider using application service tokens for production
- Rotate tokens periodically

## Troubleshooting

### Can't Create Account

- Check if registration is enabled on your Matrix server
- May need admin to create accounts
- Try using admin API if you have access

### Invalid Access Token

- Token may have expired
- Re-login to get new token
- Check token format (should start with `syt_`)

### Can't Join Room

- Ensure room is public or bot is invited
- Check room ID is correct
- Verify bot has joined room: `matrix-commander --room-list`

## Next Steps

Once Matrix setup is complete:

1. Test bot posting to rooms
2. Integrate with MCP server
3. Update agent workflows to use Matrix instead of files
4. Set up mobile Element app for triggers
5. Deploy to other VMs
