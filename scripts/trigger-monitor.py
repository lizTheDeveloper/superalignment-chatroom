#!/usr/bin/env python3
"""
Trigger Monitor - Watches chatroom/triggers.txt and launches agents
Sequences agent launches with delays based on message order.
Uses Haiku to make deterministic tool calls for message delivery.
"""

import os
import sys
import re
import json
import time
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Configuration
CHATROOM_DIR = Path(__file__).parent.parent / "chatroom"
TRIGGERS_FILE = CHATROOM_DIR / "triggers.txt"
STATE_FILE = Path(__file__).parent.parent / "matrix-credentials" / "trigger-state.json"
PROJECT_DIR = Path("/Users/annhoward/src/superalignmenttoutopia")

# Auto-detect Claude binary (works on Mac and Linux)
def find_claude_bin():
    """Find Claude Code binary in PATH or common locations."""
    # Try system PATH first
    import shutil
    claude_path = shutil.which("claude")
    if claude_path:
        return claude_path

    # Common Mac locations
    mac_paths = [
        "/Users/annhoward/.nvm/versions/node/v22.12.0/bin/claude",
        Path.home() / ".nvm" / "versions" / "node" / "v22.12.0" / "bin" / "claude",
    ]

    for path in mac_paths:
        path_obj = Path(path)
        if path_obj.exists():
            return str(path_obj)

    # Fallback to system claude
    return "claude"

CLAUDE_BIN = find_claude_bin()

# Agent sequencing delays (in seconds)
AGENT_DELAYS = {
    "sylvia": 0,      # Research skeptic goes first
    "cynthia": 5,     # Researcher goes second
    "roy": 10,        # Simulation maintainer third
    "moss": 15,       # Feature implementer fourth
    "tessa": 20,      # UX designer fifth
    "historian": 25,  # Documentation sixth
    "architect": 30,  # Roadmap manager seventh
    "ray": 35,        # Sci-fi visionary eighth
    "orchestrator": 40  # Orchestrator last to coordinate
}

# Agent MCP config paths
AGENT_MCP_CONFIGS = {
    "sylvia": "/Users/annhoward/src/superalignment-chatroom/.claude/agents/mcp-configs/matrix.mcp.json",
    "roy": "/Users/annhoward/src/superalignment-chatroom/.claude/agents/mcp-configs/matrix.mcp.json",
    "cynthia": "/Users/annhoward/src/superalignment-chatroom/.claude/agents/mcp-configs/matrix.mcp.json",
    "moss": "/Users/annhoward/src/superalignment-chatroom/.claude/agents/mcp-configs/minimal.mcp.json",
    "tessa": "/Users/annhoward/src/superalignment-chatroom/.claude/agents/mcp-configs/minimal.mcp.json",
    "historian": "/Users/annhoward/src/superalignment-chatroom/.claude/agents/mcp-configs/full.mcp.json",
    "architect": "/Users/annhoward/src/superalignment-chatroom/.claude/agents/mcp-configs/full.mcp.json",
    "ray": "/Users/annhoward/src/superalignment-chatroom/.claude/agents/mcp-configs/matrix.mcp.json",
    "orchestrator": "/Users/annhoward/src/superalignment-chatroom/.claude/agents/mcp-configs/full.mcp.json",
}

def load_state() -> Dict:
    """Load last processed line from state file."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"last_line": 0}
    return {"last_line": 0}

def save_state(state: Dict):
    """Save current state to file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def parse_trigger_message(line: str) -> Optional[Dict]:
    """
    Parse a trigger message line.

    Format: [TIMESTAMP] [SENDER] [STATUS] @agent1 @agent2: Message text

    Returns:
        dict with timestamp, sender, status, agents, message or None if invalid
    """
    if not line.strip():
        return None

    try:
        # Example: [2025-10-31 16:00:00] [architect] [TRIGGER] @sylvia @roy: Please review this
        parts = line.split("] ", 3)
        if len(parts) < 4:
            return None

        timestamp = parts[0].replace("[", "").strip()
        sender = parts[1].replace("[", "").strip()
        status = parts[2].replace("[", "").strip()
        content = parts[3].strip()

        # Extract agent mentions and message
        agents = re.findall(r'@(\w+)', content)
        # Remove agent mentions from message
        message = re.sub(r'@\w+\s*:?\s*', '', content).strip()

        return {
            "timestamp": timestamp,
            "sender": sender,
            "status": status,
            "agents": agents,
            "message": message,
            "raw": line
        }
    except Exception as e:
        print(f"⚠️ Error parsing line: {e}", file=sys.stderr)
        return None

def create_agent_prompt(agent_name: str, sender: str, message: str) -> str:
    """Create the prompt that will be sent to the agent via Haiku."""
    return f"""{agent_name.capitalize()} has received a trigger message:

**From:** {sender}
**Message:** {message}

Please respond to this request by:
1. Recalling your context using mcp__agent-memory__recall_context with agent_id='{agent_name}'
2. Reading the full message and understanding the task
3. Taking appropriate action based on your role
4. Posting your response to the appropriate chatroom channel
5. Updating your memory with this task

Use the chatroom and agent-memory MCP tools as needed."""

def launch_agent_with_haiku(
    agent_name: str,
    sender: str,
    message: str,
    delay: int = 0
) -> subprocess.Popen:
    """
    Launch a Claude Code instance for an agent using Haiku for message delivery.

    Args:
        agent_name: Agent to launch (e.g., 'sylvia', 'roy')
        sender: Who sent the trigger message
        message: The trigger message content
        delay: Delay in seconds before launch

    Returns:
        subprocess.Popen object for the launched process
    """
    if delay > 0:
        print(f"⏱️  Waiting {delay}s before launching {agent_name}...")
        time.sleep(delay)

    # Get agent-specific MCP config
    mcp_config = AGENT_MCP_CONFIGS.get(agent_name.lower())
    if not mcp_config:
        print(f"❌ No MCP config for agent '{agent_name}'", file=sys.stderr)
        return None

    # Create the prompt for Haiku to deliver
    prompt = create_agent_prompt(agent_name, sender, message)

    # Build claude command with Haiku for deterministic tool call
    cmd = [
        CLAUDE_BIN,
        "--print",  # Headless mode
        "--dangerously-skip-permissions",  # Skip all permissions
        "--model", "haiku",  # Use Haiku for cost efficiency
        "--output-format", "json",  # Deterministic JSON output
        "--mcp-config", mcp_config,  # Agent-specific MCP config
        "--strict-mcp-config",  # Don't inherit main config
        prompt
    ]

    # Log launch
    log_file = Path(__file__).parent.parent / "logs" / f"trigger_{agent_name}_{int(time.time())}.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"🚀 Launching {agent_name} (Haiku, skip-permissions)")
    print(f"   MCP config: {mcp_config}")
    print(f"   Log: {log_file}")

    # Launch process
    with open(log_file, 'w') as f:
        f.write(f"=== Trigger Launch: {agent_name} ===\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"Sender: {sender}\n")
        f.write(f"Message: {message}\n")
        f.write(f"Command: {' '.join(cmd)}\n\n")
        f.write("=== Claude Output ===\n")
        f.flush()

        proc = subprocess.Popen(
            cmd,
            cwd=str(PROJECT_DIR),
            stdout=f,
            stderr=subprocess.STDOUT,
            text=True
        )

    print(f"✅ {agent_name} launched (PID: {proc.pid})")
    return proc

def process_trigger_messages(dry_run: bool = False) -> List[Tuple[str, str, str, int]]:
    """
    Process new trigger messages and return launch queue.

    Returns:
        List of (agent_name, sender, message, delay) tuples
    """
    if not TRIGGERS_FILE.exists():
        print(f"⚠️ Triggers file not found: {TRIGGERS_FILE}")
        return []

    state = load_state()
    last_line = state.get("last_line", 0)

    # Read all lines
    with open(TRIGGERS_FILE, 'r') as f:
        lines = f.readlines()

    # Process new lines only
    new_lines = lines[last_line:]
    if not new_lines:
        return []

    print(f"📋 Processing {len(new_lines)} new trigger messages")

    launch_queue = []

    for i, line in enumerate(new_lines):
        msg = parse_trigger_message(line)
        if not msg:
            continue

        print(f"\n📨 Trigger: {msg['sender']} → {', '.join(msg['agents'])}")
        print(f"   Message: {msg['message'][:100]}...")

        # Queue each mentioned agent with their delay
        for agent in msg['agents']:
            agent_lower = agent.lower()
            delay = AGENT_DELAYS.get(agent_lower, 0)

            if dry_run:
                print(f"   [DRY RUN] Would launch {agent} with delay {delay}s")
            else:
                launch_queue.append((agent, msg['sender'], msg['message'], delay))

    # Update state
    if not dry_run:
        state['last_line'] = last_line + len(new_lines)
        state['last_check'] = datetime.now().isoformat()
        save_state(state)

    return launch_queue

def run_monitor(interval: int = 30, dry_run: bool = False):
    """
    Run the trigger monitor continuously.

    Args:
        interval: Check interval in seconds
        dry_run: If True, don't actually launch agents
    """
    print(f"🔍 Starting Trigger Monitor")
    print(f"   Watching: {TRIGGERS_FILE}")
    print(f"   Check interval: {interval}s")
    print(f"   Dry run: {dry_run}")
    print(f"   Agent delays: {AGENT_DELAYS}")

    try:
        while True:
            launch_queue = process_trigger_messages(dry_run)

            if launch_queue:
                print(f"\n🚀 Launching {len(launch_queue)} agents...")

                # Sort by delay to launch in sequence
                launch_queue.sort(key=lambda x: x[3])

                processes = []
                for agent, sender, message, delay in launch_queue:
                    proc = launch_agent_with_haiku(agent, sender, message, delay)
                    if proc:
                        processes.append((agent, proc))

                # Wait for all processes to complete
                print(f"\n⏳ Waiting for {len(processes)} agents to complete...")
                for agent, proc in processes:
                    proc.wait()
                    print(f"✅ {agent} completed (exit code: {proc.returncode})")

            print(f"\n⏱️  Sleeping {interval}s until next check...")
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n🛑 Monitor stopped by user")

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Trigger Monitor - Launch agents from chatroom triggers"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Check interval in seconds (default: 30)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse messages but don't launch agents"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process once and exit"
    )

    args = parser.parse_args()

    if args.once:
        launch_queue = process_trigger_messages(args.dry_run)
        if launch_queue and not args.dry_run:
            # Sort by delay
            launch_queue.sort(key=lambda x: x[3])

            processes = []
            for agent, sender, message, delay in launch_queue:
                proc = launch_agent_with_haiku(agent, sender, message, delay)
                if proc:
                    processes.append((agent, proc))

            # Wait for all to complete
            for agent, proc in processes:
                proc.wait()
                print(f"✅ {agent} completed (exit code: {proc.returncode})")
    else:
        run_monitor(interval=args.interval, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
