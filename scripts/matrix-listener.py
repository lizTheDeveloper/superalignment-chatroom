#!/usr/bin/env python3
"""
Matrix Message Listener
Listens to Matrix rooms and spawns agents based on @mentions or writes to triggers.txt.

Architecture:
- Monitors all configured Matrix rooms
- Detects @mentions of agents (e.g., @agent-sylvia:themultiverse.school)
- Writes trigger messages to chatroom/triggers.txt
- Uses message deduplication to prevent double-spawning
- Skips messages with bridge metadata (prevents echo loops)

Usage:
    python3 matrix-listener.py [--agent AGENT_NAME] [--interval SECONDS]
"""

import os
import sys
import re
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Set
from datetime import datetime

from nio import AsyncClient, RoomMessageText, MatrixRoom, RoomMessage, SyncResponse
from dotenv import load_dotenv

# Import deduplication system
from message_deduplication import (
    generate_message_id,
    is_message_processed,
    mark_message_processed
)

# Load environment variables
env_path = Path.home() / ".superalignment-env"
if env_path.exists():
    load_dotenv(env_path)

# Configuration
CHATROOM_DIR = Path(__file__).parent.parent / "chatroom"
TRIGGERS_FILE = CHATROOM_DIR / "triggers.txt"
ROOMS_CONFIG_PATH = Path(__file__).parent.parent / "matrix-credentials" / "matrix-rooms.json"
HOMESERVER = os.getenv("MATRIX_HOMESERVER", "https://matrix.themultiverse.school")

# Agent name mapping (Matrix ID → internal name)
AGENT_MATRIX_IDS = {
    "@agent-orchestrator:themultiverse.school": "orchestrator",
    "@agent-sylvia:themultiverse.school": "sylvia",
    "@agent-roy:themultiverse.school": "roy",
    "@agent-cynthia:themultiverse.school": "cynthia",
    "@agent-moss:themultiverse.school": "moss",
    "@agent-tessa:themultiverse.school": "tessa",
    "@agent-historian:themultiverse.school": "historian",
    "@agent-architect:themultiverse.school": "architect",
    "@agent-ray:themultiverse.school": "ray",
}

# Reverse mapping for detection
AGENT_NAMES = set(AGENT_MATRIX_IDS.values())

# Load room mappings
def load_room_mappings() -> Dict[str, str]:
    """Load channel -> room_id mappings from JSON file."""
    try:
        with open(ROOMS_CONFIG_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Room mappings not found: {ROOMS_CONFIG_PATH}")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing room mappings: {e}")
        return {}

ROOM_MAPPINGS = load_room_mappings()
# Reverse mapping: room_id -> channel
ROOM_ID_TO_CHANNEL = {v: k for k, v in ROOM_MAPPINGS.items()}

async def get_matrix_client(agent_name: str = "monitor") -> Optional[AsyncClient]:
    """
    Create and configure Matrix client for listener bot.

    Args:
        agent_name: Agent to authenticate as (default: monitor)

    Returns:
        Authenticated AsyncClient or None if token missing
    """
    token = os.getenv(f"MATRIX_TOKEN_{agent_name.upper()}")
    if not token:
        print(f"❌ Error: MATRIX_TOKEN_{agent_name.upper()} not set in ~/.superalignment-env")
        return None

    user_id = f"@agent-{agent_name.lower()}:themultiverse.school"
    client = AsyncClient(HOMESERVER, user_id)
    client.access_token = token
    client.device_id = f"{agent_name.upper()}_LISTENER_DEVICE"

    return client

def extract_agent_mentions(text: str) -> Set[str]:
    """
    Extract agent mentions from message text.

    Supports formats:
    - @agent-sylvia:themultiverse.school
    - @sylvia
    - @agent-roy

    Args:
        text: Message text to parse

    Returns:
        Set of agent names mentioned
    """
    mentioned_agents = set()

    # Pattern 1: Full Matrix IDs
    for matrix_id, agent_name in AGENT_MATRIX_IDS.items():
        if matrix_id in text:
            mentioned_agents.add(agent_name)

    # Pattern 2: Short mentions (@sylvia, @roy, etc.)
    short_mentions = re.findall(r'@([\w-]+)', text)
    for mention in short_mentions:
        # Remove "agent-" prefix if present
        clean_mention = mention.replace("agent-", "").lower()
        if clean_mention in AGENT_NAMES:
            mentioned_agents.add(clean_mention)

    return mentioned_agents

def write_trigger_message(sender: str, agents: Set[str], message: str, channel: str):
    """
    Write a trigger message to triggers.txt.

    Format: [TIMESTAMP] [SENDER] [TRIGGER] @agent1 @agent2: Message

    Args:
        sender: Matrix user ID who sent the message
        agents: Set of agent names to trigger
        message: Message content
        channel: Channel name (e.g., 'coordination', 'research')
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    agent_mentions = " ".join(f"@{agent}" for agent in sorted(agents))

    # Extract username from Matrix ID (e.g., @user:domain → user)
    sender_name = sender.split(":")[0].replace("@", "")

    trigger_line = f"[{timestamp}] [{sender_name}] [TRIGGER] {agent_mentions}: {message}\n"

    # Append to triggers file
    TRIGGERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRIGGERS_FILE, 'a') as f:
        f.write(trigger_line)

    print(f"✅ Wrote trigger: {sender_name} → {', '.join(sorted(agents))}")
    print(f"   Channel: {channel}")
    print(f"   Message: {message[:80]}...")

async def message_callback(room: MatrixRoom, event: RoomMessage):
    """
    Callback for Matrix room messages.

    Args:
        room: MatrixRoom where message was sent
        event: RoomMessage event
    """
    # Only process text messages
    if not isinstance(event, RoomMessageText):
        return

    # Get channel name from room ID
    channel = ROOM_ID_TO_CHANNEL.get(room.room_id)
    if not channel:
        # Not a configured channel, ignore
        return

    # Skip messages from bridge (prevent echo)
    if hasattr(event, 'source') and isinstance(event.source.get('content', {}), dict):
        content = event.source.get('content', {})
        if 'uk.half-shot.bridge' in content:
            print(f"⏭️  Skipping bridged message in {channel}")
            return

    # Skip messages from our own bots (prevent self-triggering)
    if event.sender in AGENT_MATRIX_IDS:
        return

    # Generate message ID for deduplication
    message_id = generate_message_id(
        content=event.body,
        sender=event.sender,
        timestamp=str(event.server_timestamp),
        channel=channel
    )

    # Check for duplicate
    if is_message_processed(message_id):
        print(f"⏭️  Skipping duplicate message ID {message_id[:8]}... in {channel}")
        return

    # Extract agent mentions
    mentioned_agents = extract_agent_mentions(event.body)

    if not mentioned_agents:
        # No agents mentioned, just mark as processed and skip
        mark_message_processed(
            message_id,
            source='matrix-listener',
            metadata={
                'channel': channel,
                'sender': event.sender,
                'no_mentions': True
            }
        )
        return

    # Write trigger message
    print(f"\n📨 New message in {channel} from {event.sender}")
    print(f"   Mentioned agents: {', '.join(sorted(mentioned_agents))}")

    try:
        write_trigger_message(
            sender=event.sender,
            agents=mentioned_agents,
            message=event.body,
            channel=channel
        )

        # Mark as processed
        mark_message_processed(
            message_id,
            source='matrix-listener',
            metadata={
                'channel': channel,
                'sender': event.sender,
                'agents': list(mentioned_agents)
            }
        )

    except Exception as e:
        print(f"❌ Error writing trigger: {e}")

async def run_listener(agent_name: str = "monitor", sync_interval: int = 30):
    """
    Run the Matrix listener continuously.

    Args:
        agent_name: Agent to authenticate as (default: monitor)
        sync_interval: Sync interval in seconds (default: 30)
    """
    client = await get_matrix_client(agent_name)
    if not client:
        sys.exit(1)

    if not ROOM_MAPPINGS:
        print("❌ Error: No room mappings configured")
        sys.exit(1)

    print(f"🔊 Starting Matrix Listener")
    print(f"   Agent: {agent_name}")
    print(f"   Channels: {', '.join(ROOM_MAPPINGS.keys())}")
    print(f"   Sync interval: {sync_interval}s")
    print(f"   Triggers file: {TRIGGERS_FILE}\n")

    # Register message callback
    client.add_event_callback(message_callback, RoomMessageText)

    try:
        # Initial sync
        print("⏳ Performing initial sync...")
        await client.sync(timeout=30000, full_state=True)
        print("✅ Initial sync complete\n")

        # Continuous sync loop
        while True:
            response = await client.sync(timeout=sync_interval * 1000)

            if isinstance(response, SyncResponse):
                # Check for new messages (handled by callback)
                pass

            await asyncio.sleep(1)  # Small delay between syncs

    except KeyboardInterrupt:
        print("\n🛑 Listener stopped by user")
    except Exception as e:
        print(f"\n❌ Error in listener: {e}")
        raise
    finally:
        await client.close()
        print("✅ Matrix client closed")

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Matrix Message Listener")
    parser.add_argument(
        "--agent",
        default="monitor",
        help="Agent to authenticate as (default: monitor)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Sync interval in seconds (default: 30)"
    )

    args = parser.parse_args()

    asyncio.run(run_listener(agent_name=args.agent, sync_interval=args.interval))

if __name__ == "__main__":
    main()
