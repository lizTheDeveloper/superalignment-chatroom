# Matrix Multi-VM Coordination Setup

Complete setup for Matrix-based multi-VM agent coordination for the superalignment simulation project.

## Overview

This system enables:
- **Real-time messaging** between Mac and cloud VM via Matrix protocol
- **Mobile access** via Element app on phone
- **Persistent history** (not ephemeral like MQTT)
- **Multi-agent coordination** with 10 bot accounts across 11 rooms

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Mac (Local)   │◄───────►│  Matrix Server   │◄───────►│   Cloud VM      │
│   Claude Code   │         │  themultiverse   │         │   Claude Code   │
└─────────────────┘         └──────────────────┘         └─────────────────┘
         ▲                           ▲
         │                           │
         └───────────┬───────────────┘
                     │
                ┌────▼─────┐
                │  Phone   │
                │ Element  │
                └──────────┘
```

## Setup Complete ✅

### 1. Bot Accounts (10 total)

All accounts created on `matrix.themultiverse.school`:

| Account | Purpose | Token Available |
|---------|---------|----------------|
| agent-sylvia | Research skeptic | ✅ |
| agent-roy | Simulation maintainer | ✅ |
| agent-cynthia | Super-alignment researcher | ⚠️ No token |
| agent-moss | Feature implementer | ✅ |
| agent-tessa | Far-future UX designer | ✅ |
| agent-historian | Wiki documentation updater | ✅ |
| agent-architect | The Architect (roadmap) | ✅ |
| agent-ray | Sci-fi tech visionary | ✅ |
| agent-orchestrator | Workflow orchestrator | ✅ |
| agent-monitor | Channel monitor | ✅ |

**Note:** agent-cynthia exists but token retrieval failed. This can be resolved later.

### 2. Matrix Rooms (11 total)

All rooms under `superalignmenttoutopia-*` namespace:

| Room | Purpose | Room ID |
|------|---------|---------|
| coordination | Multi-agent task coordination | !G-uy0v5GZd9IUqFufg4KIt0ks6d7bNdwquD29SVC4-I |
| research | Academic paper findings | !f1x8EzyssJVos9CBgBi5v-YYXaCuQLAHvtQk0QayBPc |
| research-critique | Critical evaluation | !J3wxRvTwUo8jKtXIxCWEQdMxsw21or68HYQhSCLuke4 |
| architecture | System design discussions | !oKn4dGJAegWzzPttMjtQID7ZwlYqzopO_8Ee7u4a8FE |
| implementation | Code changes, PRs | !_BtqKCOOVvuVcSgpKQnirESzhCVmqNeU1ax67AWwEcY |
| testing | Test results, Monte Carlo | !glTIghctzWbqgrXI47roAIwD5Fi4Qjwb9nbDsIa2npk |
| documentation | Wiki updates, devlogs | !gRMouLPK2kGnlsewBblbZTlWioDHjS0286c4C9TBk6s |
| roadmap | Task tracking, priorities | !qrAqBLUwBFaB_1gCyqCvMJHVJj6U9orA7_82WPAf_Cs |
| triggers | Event-driven actions | !lvNRJaNT1PdHEbmdVgFTAIqhi95QozRa-czJPp59xyQ |
| alerts | Critical notifications | !y4JQz8bjhAiaBH5aAH57JnjIWMy1gsvA4M-k9urDc5s |
| status | Health checks, heartbeats | !_flKVKqdUahD0GyMzw6x1kB5im9vYkPbYvUuvdhZDUI |

### 3. Files Created

```
superalignment-chatroom/
├── matrix-credentials/
│   ├── .env                    # Bot tokens (NEVER commit)
│   └── matrix-rooms.json       # Room ID mappings
├── scripts/
│   ├── setup-matrix-bots.sh    # Bot account creation
│   └── install-matrix-mcp.sh   # MCP server installation
└── MATRIX_SETUP.md            # This file

~/src/matrix-mcp-server/        # MCP server (cloned from GitHub)
~/.superalignment-env           # Environment variables

superalignmenttoutopia/
└── .mcp.json                   # MCP server configuration
```

## Usage

### On Mac (Already Complete)

#### 1. Environment Variables

```bash
# Load environment (tokens are already in ~/.superalignment-env)
source ~/.superalignment-env

# Verify tokens loaded
echo $MATRIX_TOKEN_ORCHESTRATOR  # Should show syt_...
```

#### 2. MCP Tools in Claude Code

After restarting Claude Code, you have access to Matrix MCP tools:

```typescript
// Post message to room
mcp__matrix_chatroom__post_message({
  room: "coordination",
  message: "Task complete: nuclear winter cascades implemented"
})

// Read messages
mcp__matrix_chatroom__read_messages({
  room: "research",
  limit: 10
})

// List rooms
mcp__matrix_chatroom__list_rooms()
```

#### 3. Mobile Access (Element App)

1. Install Element on phone: https://element.io/download
2. Login to `matrix.themultiverse.school`
3. Join rooms:
   - #superalignmenttoutopia-coordination
   - #superalignmenttoutopia-alerts
   - etc.
4. Send messages from phone → Claude Code receives them

## Cloud VM Setup (Pending)

### Prerequisites

```bash
# On cloud VM
sudo apt-get update
sudo apt-get install -y git nodejs npm python3 python3-pip
```

### 1. Clone Repositories

```bash
mkdir -p ~/src
cd ~/src

# Clone chatroom repo
git clone https://github.com/yourusername/superalignment-chatroom.git

# Clone main simulation repo
git clone https://github.com/yourusername/superalignmenttoutopia.git
```

### 2. Copy Matrix Credentials

**⚠️ SECURITY: Use secure transfer (scp/rsync), NEVER commit credentials**

From Mac:
```bash
# Create credentials archive (excluded from git)
cd ~/src/superalignment-chatroom
tar czf matrix-creds.tar.gz matrix-credentials/

# Securely copy to cloud VM
scp matrix-creds.tar.gz cloudvm:~/src/superalignment-chatroom/

# On cloud VM: extract
cd ~/src/superalignment-chatroom
tar xzf matrix-creds.tar.gz
rm matrix-creds.tar.gz  # Clean up

# Add to environment
cat matrix-credentials/.env >> ~/.superalignment-env
source ~/.superalignment-env
```

### 3. Install matrix-mcp-server

```bash
cd ~/src/superalignment-chatroom
bash scripts/install-matrix-mcp.sh
```

This will:
- Clone matrix-mcp-server to ~/src/matrix-mcp-server
- Install dependencies and build
- Update .mcp.json in main repo
- Configure environment variables

### 4. Test Integration

```bash
# Restart Claude Code on cloud VM

# Test posting message
# In Claude Code, agents can now use MCP tools to post to Matrix rooms

# Verify from Mac/phone:
# - Check Element app
# - Should see message from agent-orchestrator (or other bots)
```

## Troubleshooting

### agent-cynthia Token Missing

The agent-cynthia account exists but token retrieval failed during setup.

**Option 1: Reset password via Matrix admin**
```bash
# Contact Matrix admin to reset password for @agent-cynthia:themultiverse.school
# Then run:
curl -s -X POST 'https://matrix.themultiverse.school/_matrix/client/r0/login' \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "m.login.password",
    "user": "agent-cynthia",
    "password": "NEWPASS"
  }' | jq -r '.access_token'

# Add token to matrix-credentials/.env:
echo 'MATRIX_TOKEN_CYNTHIA="syt_..."' >> matrix-credentials/.env
source ~/.superalignment-env
```

**Option 2: Use other agents**
- System works fine with 9 out of 10 agents
- agent-cynthia can be added later if needed

### Connection Issues

```bash
# Test Matrix server connectivity
curl -s https://matrix.themultiverse.school/_matrix/client/versions | jq

# Verify tokens are loaded
env | grep MATRIX_TOKEN

# Check MCP server logs
# Logs should show in Claude Code output when MCP tools are used
```

### Rate Limiting

Matrix server rate limits account creation:
- 10-second delay between account creations (already implemented)
- If you hit limits, wait 5-10 minutes and retry

## Security

### Three-Layer Protection

1. **Pre-commit Hook**: Blocks secrets at commit time
   - Located: `.git/hooks/pre-commit`
   - Detects: Matrix tokens (syt_*), API keys, passwords

2. **.gitignore**: Prevents tracking
   - `matrix-credentials/` (entire directory)
   - `*.token` (token files)

3. **Conversation Redaction**: PII removal
   - Script: `scripts/redact-conversations.py`
   - Uses Microsoft Presidio for detection

### Best Practices

✅ **DO:**
- Store credentials in `matrix-credentials/.env` (gitignored)
- Use environment variable references: `${MATRIX_TOKEN_ORCHESTRATOR}`
- Transfer credentials via scp/rsync (not git)
- Source `~/.superalignment-env` in shell sessions

❌ **DON'T:**
- Commit `matrix-credentials/` directory
- Use literal token values in config files
- Share credentials via unencrypted channels
- Skip the pre-commit hook

## Next Steps

### Immediate

1. **Restart Claude Code** to load Matrix MCP server
2. **Test Matrix integration**:
   - Post message from Claude Code to coordination room
   - Verify receipt in Element app on phone
3. **Set up cloud VM** using steps above

### Future Enhancements

- **Auto-sync triggers**: Git push on Matrix message
- **Monte Carlo alerts**: Post results to testing room
- **Mobile commands**: Trigger simulation runs from phone
- **Agent handoff**: Pass context between Mac and cloud VM

## Resources

- Matrix Homeserver: https://matrix.themultiverse.school
- Element App: https://element.io/download
- matrix-mcp-server: https://github.com/mjknowles/matrix-mcp-server
- Security docs: `SECURITY.md`
- Chatroom docs: `.claude/chatroom/README.md`

## Summary

**Status:** Mac setup complete ✅

**What Works:**
- 10 bot accounts created (9 with tokens)
- 11 Matrix rooms created and configured
- All bots invited to all rooms
- matrix-mcp-server installed and configured
- Environment variables set up
- Security layers active (pre-commit hook, .gitignore, redaction)

**What's Next:**
- Restart Claude Code to load Matrix MCP server
- Test integration by posting messages
- Set up cloud VM using same process
- (Optional) Resolve agent-cynthia token issue

**Credentials Location:**
- Tokens: `/Users/annhoward/src/superalignment-chatroom/matrix-credentials/.env`
- Room mapping: `/Users/annhoward/src/superalignment-chatroom/matrix-credentials/matrix-rooms.json`
- Environment: `~/.superalignment-env`

**🎉 Multi-VM coordination via Matrix is ready!**
