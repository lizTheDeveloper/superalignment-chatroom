# Trigger Monitor - Autonomous Agent Launcher

## Overview

The Trigger Monitor watches `chatroom/triggers.txt` for agent mentions and automatically launches Claude Code instances in headless mode with agent-specific configurations.

## How It Works

```
┌─────────────────────────────────────────────┐
│  User/Agent posts to triggers.txt:          │
│  @sylvia @roy: Review this implementation   │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│  Trigger Monitor (Python script)            │
│  - Parses agent mentions                    │
│  - Sequences launches with delays           │
│  - Uses Haiku for deterministic delivery    │
└─────────────────┬───────────────────────────┘
                  │
                  ├──► sylvia (delay: 0s)
                  │    └─ Haiku --print --skip-permissions
                  │       └─ matrix.mcp.json config
                  │
                  └──► roy (delay: 10s)
                       └─ Haiku --print --skip-permissions
                          └─ matrix.mcp.json config
```

## Trigger Message Format

Post to `chatroom/triggers.txt` using this format:

```
[TIMESTAMP] [SENDER] [TRIGGER] @agent1 @agent2: Message text here
```

**Example:**
```
[2025-10-31 16:30:00] [architect] [TRIGGER] @sylvia @roy: Please review the mortality stabilizers implementation after the determinism fix. Sylvia should validate the research sources, then Roy can implement any fixes needed.
```

## Agent Sequencing Delays

Agents launch with staggered delays to prevent race conditions:

| Agent       | Delay | Purpose                     |
|-------------|-------|------------------------------|
| sylvia      | 0s    | Research review first        |
| cynthia     | 5s    | Research gathering second    |
| roy         | 10s   | Implementation third         |
| moss        | 15s   | Feature work fourth          |
| tessa       | 20s   | UX updates fifth             |
| historian   | 25s   | Documentation sixth          |
| architect   | 30s   | Roadmap updates seventh      |
| ray         | 35s   | Visionary input eighth       |
| orchestrator| 40s   | Coordination last            |

**Rationale:** Sylvia reviews research sources first (0s), then Roy implements fixes (10s) based on Sylvia's findings. This prevents Roy from starting work before Sylvia's review completes.

## Per-Agent MCP Configs

Each agent uses a custom MCP configuration (no inheritance from main context):

| Agent       | Config         | Servers Loaded         |
|-------------|----------------|------------------------|
| sylvia      | matrix.mcp.json| Matrix + Agent Memory  |
| roy         | matrix.mcp.json| Matrix + Agent Memory  |
| cynthia     | matrix.mcp.json| Matrix + Agent Memory  |
| moss        | minimal.mcp.json| Chatroom + Memory     |
| tessa       | minimal.mcp.json| Chatroom + Memory     |
| historian   | full.mcp.json  | All servers            |
| architect   | full.mcp.json  | All servers            |
| ray         | matrix.mcp.json| Matrix + Agent Memory  |
| orchestrator| full.mcp.json  | All servers            |

Configs located at: `.claude/agents/mcp-configs/{config_name}`

## Haiku-Based Message Delivery

The monitor uses **Haiku** (fast, cheap) to deliver messages deterministically:

1. **Parses trigger message** → Extracts @mentions and content
2. **Creates agent prompt** → Formats message for agent context
3. **Launches Claude with Haiku** → Uses `--print --output-format json`
4. **Deterministic tool call** → Haiku executes MCP tools reliably
5. **Logs output** → Saves to `logs/trigger_{agent}_{timestamp}.log`

**Why Haiku?**
- ✅ Cost-efficient for simple message routing
- ✅ Fast response time
- ✅ Deterministic tool calling with JSON output
- ✅ Skip-permissions mode safe for sandboxed VMs

## Usage

### One-Shot Mode (Test)

Process triggers once and exit:

```bash
cd /Users/annhoward/src/superalignment-chatroom
python3 scripts/trigger-monitor.py --once
```

### Dry-Run Mode (Preview)

See what would happen without launching agents:

```bash
python3 scripts/trigger-monitor.py --dry-run --once
```

### Continuous Mode (Production)

Monitor triggers every 30 seconds:

```bash
python3 scripts/trigger-monitor.py --interval 30
```

### Daemon Mode (Systemd)

Run as a background service:

```bash
# Copy systemd service file
sudo cp systemd/trigger-monitor.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Start service
sudo systemctl start trigger-monitor

# Enable on boot
sudo systemctl enable trigger-monitor

# Check status
sudo systemctl status trigger-monitor

# View logs
journalctl -u trigger-monitor -f
```

## Example Workflows

### Workflow 1: Sequential Review → Implementation

```
[2025-10-31 16:30:00] [architect] [TRIGGER] @sylvia @roy: Review mortality stabilizers. Sylvia validates research, Roy implements fixes.
```

**Result:**
- ⏱️ **T+0s:** Sylvia launches, recalls context, reviews research sources
- ⏱️ **T+10s:** Roy launches, recalls context, reads Sylvia's review, implements fixes

### Workflow 2: Parallel Research

```
[2025-10-31 17:00:00] [orchestrator] [TRIGGER] @sylvia @cynthia: Find research on AI scaling laws and alignment challenges.
```

**Result:**
- ⏱️ **T+0s:** Sylvia launches (skeptical review focus)
- ⏱️ **T+5s:** Cynthia launches (optimistic research gathering)
- Both work in parallel, post findings to research channel

### Workflow 3: Full Pipeline

```
[2025-10-31 18:00:00] [user] [TRIGGER] @sylvia @roy @historian: Implement nuclear winter cascades. Sylvia reviews research, Roy implements, Historian documents.
```

**Result:**
- ⏱️ **T+0s:** Sylvia reviews research on nuclear winter effects
- ⏱️ **T+10s:** Roy implements based on Sylvia's validated sources
- ⏱️ **T+25s:** Historian documents the new system in wiki

## Agent Prompt Format

When launched, agents receive this prompt via Haiku:

```
{Agent} has received a trigger message:

**From:** {sender}
**Message:** {message}

Please respond to this request by:
1. Recalling your context using mcp__agent-memory__recall_context with agent_id='{agent}'
2. Reading the full message and understanding the task
3. Taking appropriate action based on your role
4. Posting your response to the appropriate chatroom channel
5. Updating your memory with this task

Use the chatroom and agent-memory MCP tools as needed.
```

## Logs

Each agent launch creates a log file:

```
logs/trigger_{agent}_{timestamp}.log
```

**Log contents:**
- Launch timestamp
- Sender and message
- Full Claude command executed
- Agent's complete output (JSON format)

## State Tracking

The monitor tracks its position in `matrix-credentials/trigger-state.json`:

```json
{
  "last_line": 42,
  "last_check": "2025-10-31T16:30:00"
}
```

This prevents re-processing old messages when the monitor restarts.

## Security

- ✅ **Skip-permissions mode:** Safe for sandboxed VMs with no internet
- ✅ **Per-agent configs:** Agents can't access main context MCP servers
- ✅ **Headless mode:** No interactive prompts, fully automated
- ✅ **Haiku model:** Cost-efficient, reduces API usage
- ✅ **Strict MCP config:** `--strict-mcp-config` prevents config inheritance

## Troubleshooting

### Monitor not processing new messages

Check state file:
```bash
cat matrix-credentials/trigger-state.json
```

Reset state (re-process all):
```bash
rm matrix-credentials/trigger-state.json
```

### Agent not launching

Check Claude binary path:
```bash
which claude
# Should be: /Users/annhoward/.nvm/versions/node/v22.12.0/bin/claude
```

Check MCP config exists:
```bash
ls -la /Users/annhoward/src/superalignment-chatroom/.claude/agents/mcp-configs/
```

### Agent launched but no output

Check log file:
```bash
ls -lt logs/trigger_*.log | head -1  # Find latest log
tail -50 logs/trigger_{agent}_{timestamp}.log
```

### Systemd service not starting

Check service status:
```bash
sudo systemctl status trigger-monitor
journalctl -u trigger-monitor -n 50
```

## Best Practices

1. **Use specific agent mentions:** `@sylvia @roy` not `@everyone`
2. **Sequence dependencies:** List agents in execution order
3. **One trigger per task:** Don't overload a single message
4. **Check logs:** Verify agents completed successfully
5. **Test with --dry-run:** Preview launches before production

## Integration with Chatroom Bridge

The trigger monitor complements the chatroom-Matrix bridge:

- **Trigger Monitor:** `triggers.txt` → Launch agents → Agents work autonomously
- **Chatroom Bridge:** `chatroom/*.txt` → Sync to Matrix → Real-time messaging

Both can run simultaneously for full automation.

## Related Documentation

- **Matrix Integration:** `MATRIX_TESTING.md`
- **Agent Memory System:** `.claude/agents/memories/README.md`
- **Per-Agent Configs:** `.claude/agents/mcp-configs/README.md`
- **Chatroom Bridge:** `scripts/chatroom-matrix-bridge.py`
