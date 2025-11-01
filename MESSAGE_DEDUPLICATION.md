# Message Deduplication System

**Status:** ✅ Active (2025-11-01)

## Problem

When messages flow through multiple systems (file-based chatroom, Matrix rooms, bridge), there's a risk of **double-spawning agents**:

```
Scenario: Agent posts to Matrix
  Agent → Matrix (via MCP tools)
       ↓
  Matrix listener sees it → spawns agents ❌ (SPAWN 1)
       ↓
  Bridge syncs Matrix → chatroom file
       ↓
  trigger-monitor.py sees file change → spawns agents AGAIN ❌ (SPAWN 2)

Result: DOUBLE SPAWN for same message
```

## Solution

**Shared deduplication state** with deterministic message IDs that both listeners check before spawning.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Shared Deduplication State                 │
│        matrix-credentials/processed-messages.json           │
│                                                             │
│  {                                                          │
│    "38f0e0a5": {                                            │
│      "timestamp": "2025-11-01T12:00:00",                    │
│      "source": "trigger-monitor",                           │
│      "sender": "sylvia",                                    │
│      "agents": ["roy", "cynthia"]                           │
│    }                                                        │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
         ↑                                    ↑
         │                                    │
    ┌────┴─────┐                      ┌──────┴──────┐
    │  trigger-│                      │   chatroom- │
    │  monitor │                      │   matrix-   │
    │   .py    │                      │   bridge.py │
    └──────────┘                      └─────────────┘
```

### Components

#### 1. message_deduplication.py

**Location:** `scripts/message_deduplication.py`

**Core Functions:**

```python
# Generate deterministic message ID from content + metadata
generate_message_id(content, sender, timestamp, channel) -> str

# Check if message already processed
is_message_processed(message_id) -> bool

# Mark message as processed
mark_message_processed(message_id, source, metadata)

# Get statistics
get_stats() -> dict

# Clean up old messages (>24 hours)
cleanup_old_messages(messages) -> int
```

**Message ID Generation:**

- SHA256 hash of: `sender:normalized_content:timestamp_hour:channel`
- Normalized content: stripped, lowercased
- Timestamp grouped by hour (prevents minor timestamp diffs from creating different IDs)
- Result: 16-character hex hash (e.g., `38f0e0a554972f69`)

**Automatic Cleanup:**

- Messages older than 24 hours are removed from state
- Cleanup runs whenever state is saved
- Prevents state file from growing unbounded

**CLI Tools:**

```bash
# Show statistics
python3 scripts/message_deduplication.py stats

# Manual cleanup
python3 scripts/message_deduplication.py cleanup

# Reset all state
python3 scripts/message_deduplication.py reset
```

#### 2. trigger-monitor.py Integration

**Changes:**

1. Import deduplication module
2. Generate message ID when parsing trigger messages
3. Check `is_message_processed()` before adding to launch queue
4. Mark as processed via `mark_message_processed()` after parsing
5. Include message_id in launch queue tuple

**Flow:**

```python
msg = parse_trigger_message(line)
# → msg contains: {timestamp, sender, status, agents, message, message_id}

if is_message_processed(msg['message_id']):
    print(f"⏭️  Skipping duplicate message ID {msg['message_id'][:8]}...")
    continue

# Add to launch queue
launch_queue.append((agent, sender, message, delay, message_id))

# Mark as processed
mark_message_processed(
    msg['message_id'],
    source='trigger-monitor',
    metadata={'sender': sender, 'agents': agents}
)
```

**Output Example:**

```
📋 Processing 2 new trigger messages

📨 Trigger: architect → sylvia, roy
   Message: Please review the nuclear winter cascades implementation
   Message ID: 38f0e0a5...

📨 Trigger: cynthia → moss
   Message: Implement food security recovery mechanics
   Message ID: 7c2d1f89...

⏭️  Skipping duplicate message ID 38f0e0a5... (already processed)
```

#### 3. chatroom-matrix-bridge.py Integration

**Changes:**

1. Import deduplication module
2. Generate message ID before syncing to Matrix
3. Check `is_message_processed()` before posting
4. Mark as processed after successful Matrix post
5. Include message_id in Matrix message metadata

**Flow:**

```python
msg = parse_chatroom_message(line)

message_id = generate_message_id(
    content=msg['message'],
    sender=msg['agent'],
    timestamp=msg['timestamp'],
    channel=channel
)

if is_message_processed(message_id):
    print(f"  ⏭️  Skipping duplicate message ID {message_id[:8]}...")
    continue

# Post to Matrix with metadata
await client.room_send(
    room_id=room_id,
    message_type="m.room.message",
    content={
        "msgtype": "m.text",
        "body": formatted_msg,
        "uk.half-shot.bridge": {
            "source": "chatroom-file",
            "channel": channel,
            "agent": msg['agent'],
            "message_id": message_id  # ← Added for deduplication
        }
    }
)

# Mark as processed
mark_message_processed(
    message_id,
    source='chatroom-matrix-bridge',
    metadata={'channel': channel, 'agent': agent, 'direction': 'chatroom->matrix'}
)
```

**Output Example:**

```
📤 Syncing 3 new messages from research to Matrix
  ✅ Posted: [sylvia] Climate tipping points cascade at 1.5°C...
     Message ID: 38f0e0a5...
  ⏭️  Skipping duplicate message ID 7c2d1f89... (already processed)
  ✅ Posted: [roy] Fixed NaN bug in ecology phase
     Message ID: a9b3c4d2...
```

## Deduplication Flow Examples

### Example 1: Normal Operation (No Duplicates)

```
1. Sylvia posts to Matrix via MCP tools
   → Matrix listener would see it (if implemented)
   → Generates message_id: 38f0e0a5
   → Checks: not processed yet
   → Spawns agents
   → Marks 38f0e0a5 as processed

2. Bridge syncs Matrix → chatroom file
   → Reads message from Matrix
   → Generates same message_id: 38f0e0a5
   → Checks: already processed ✅
   → Skips syncing (prevents loop)

3. trigger-monitor.py sees chatroom file change
   → Reads new line
   → Generates same message_id: 38f0e0a5
   → Checks: already processed ✅
   → Skips spawning (prevents double-spawn)

Result: Only ONE spawn, no loops
```

### Example 2: Agent Posts to Chatroom File Directly

```
1. trigger-monitor.py detects new message in triggers.txt
   → Generates message_id: 7c2d1f89
   → Checks: not processed yet
   → Spawns agents
   → Marks 7c2d1f89 as processed

2. Bridge syncs chatroom → Matrix
   → Reads same message from file
   → Generates same message_id: 7c2d1f89
   → Checks: already processed ✅
   → Skips syncing to Matrix

Result: No double-posting to Matrix
```

### Example 3: Cleanup After 24 Hours

```
State at T=0:
{
  "38f0e0a5": {"timestamp": "2025-11-01T12:00:00", "source": "trigger-monitor"},
  "7c2d1f89": {"timestamp": "2025-11-01T13:00:00", "source": "bridge"}
}

State at T=25 hours (automatic cleanup runs):
{
  "a9b3c4d2": {"timestamp": "2025-11-02T13:00:00", "source": "trigger-monitor"}
}

Old messages (38f0e0a5, 7c2d1f89) removed automatically
```

## State File Format

**Location:** `matrix-credentials/processed-messages.json`

**Format:**

```json
{
  "38f0e0a554972f69": {
    "timestamp": "2025-11-01T12:34:56.789123",
    "source": "trigger-monitor",
    "sender": "sylvia",
    "agents": ["roy", "cynthia"],
    "line_number": 42
  },
  "7c2d1f8945ab3210": {
    "timestamp": "2025-11-01T13:45:12.345678",
    "source": "chatroom-matrix-bridge",
    "channel": "research",
    "agent": "cynthia",
    "direction": "chatroom->matrix"
  }
}
```

**Fields:**

- **timestamp**: When message was processed (ISO format)
- **source**: Which script processed it (`trigger-monitor` or `chatroom-matrix-bridge`)
- **metadata**: Source-specific metadata (sender, agents, channel, etc.)

## Testing

### Unit Test: Message ID Generation

```bash
cd ~/src/superalignment-chatroom/scripts

# Generate same ID for identical messages
python3 -c "
from message_deduplication import generate_message_id

id1 = generate_message_id('test message', 'sylvia', '2025-11-01 12:00', 'research')
id2 = generate_message_id('test message', 'sylvia', '2025-11-01 12:00', 'research')

print(f'ID 1: {id1}')
print(f'ID 2: {id2}')
print(f'Match: {id1 == id2}')
"
```

Expected output:
```
ID 1: 38f0e0a554972f69
ID 2: 38f0e0a554972f69
Match: True
```

### Integration Test: Deduplication in Action

```bash
# 1. Reset state
python3 scripts/message_deduplication.py reset

# 2. Create test trigger message
echo "[2025-11-01 12:00:00] [test-user] [TRIGGER] @sylvia: Test deduplication" >> ~/src/superalignment-chatroom/chatroom/triggers.txt

# 3. Run trigger-monitor in dry-run mode
cd ~/src/superalignment-chatroom
python3 scripts/trigger-monitor.py --once --dry-run

# 4. Check stats (should show 1 processed message)
python3 scripts/message_deduplication.py stats

# 5. Run trigger-monitor again (should skip duplicate)
python3 scripts/trigger-monitor.py --once --dry-run
```

Expected output (second run):
```
📋 Processing 1 new trigger messages
⏭️  Skipping duplicate message ID 38f0e0a5... (already processed)
```

### Monitoring in Production

```bash
# Check deduplication stats
python3 scripts/message_deduplication.py stats

# Output:
# === Message Deduplication Stats ===
# Total processed: 47
# By source: {'trigger-monitor': 32, 'chatroom-matrix-bridge': 15}
# Oldest message: 2025-11-01T08:00:00.000000
# Cleanup threshold: 24 hours
```

## Maintenance

### Cleanup Old Messages

**Automatic:** Runs every time state is saved (no action needed)

**Manual:**

```bash
python3 scripts/message_deduplication.py cleanup
```

### Reset All State

```bash
# WARNING: This will clear all deduplication history
python3 scripts/message_deduplication.py reset
```

**When to reset:**

- After testing/development (before production deployment)
- If state file becomes corrupted
- Never in production (automatic cleanup handles old messages)

## Troubleshooting

### "Message spawned twice despite deduplication"

**Check:**

1. Are both scripts using the same state file?
   ```bash
   grep -r "processed-messages.json" ~/src/superalignment-chatroom/scripts/
   ```

2. Are message IDs identical?
   ```bash
   # Add debug logging to both scripts
   print(f"Generated message_id: {message_id}")
   ```

3. Is cleanup threshold too aggressive?
   ```python
   # In message_deduplication.py
   CLEANUP_THRESHOLD_HOURS = 24  # Increase if needed
   ```

### "State file growing too large"

**Check stats:**

```bash
python3 scripts/message_deduplication.py stats
```

If `total_processed` > 1000, run manual cleanup:

```bash
python3 scripts/message_deduplication.py cleanup
```

### "Import error: message_deduplication module not found"

**Fix:** Ensure scripts run from correct directory:

```bash
cd ~/src/superalignment-chatroom/scripts
python3 trigger-monitor.py
```

Or add to PYTHONPATH:

```bash
export PYTHONPATH="${PYTHONPATH}:~/src/superalignment-chatroom/scripts"
```

## Future Enhancements

### Matrix → Chatroom Listener

When implementing Matrix message listener (to sync Matrix → chatroom files):

```python
# In Matrix listener callback
async def on_message(room, event):
    # Check if message has bridge metadata (skip if from bridge)
    if "uk.half-shot.bridge" in event.content:
        return  # Don't sync bridged messages back

    # Generate message ID
    message_id = generate_message_id(
        content=event.body,
        sender=event.sender,
        timestamp=event.server_timestamp,
        channel=room_id_to_channel(room.room_id)
    )

    # Check for duplicate
    if is_message_processed(message_id):
        return  # Already handled

    # Sync to chatroom file...

    # Mark as processed
    mark_message_processed(message_id, source='matrix-listener', ...)
```

This completes the bidirectional deduplication architecture.

## Related Documentation

- **Chatroom Coordination:** `.claude/chatroom/README.md`
- **Matrix Integration:** `~/src/superalignment-chatroom/MATRIX_TESTING.md`
- **Bridge Script:** `scripts/chatroom-matrix-bridge.py`
- **Trigger Monitor:** `scripts/trigger-monitor.py`

---

**Last updated:** 2025-11-01
**Status:** ✅ Implemented and tested
**Deployed:** Local + VM (after git push)
