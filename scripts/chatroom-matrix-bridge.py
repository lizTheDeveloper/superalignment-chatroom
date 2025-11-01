#!/usr/bin/env python3
"""
Chatroom-Matrix Bridge
Syncs file-based chatroom channels to Matrix rooms bidirectionally.

Features:
- Monitors chatroom/ directory for new messages
- Posts new messages to corresponding Matrix rooms
- Optionally syncs Matrix messages back to chatroom files
- Tracks last sync position per channel
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from nio import AsyncClient, RoomMessageText
from dotenv import load_dotenv

# Load environment variables
env_path = Path.home() / ".superalignment-env"
if env_path.exists():
    load_dotenv(env_path)

# Configuration
CHATROOM_DIR = Path(__file__).parent.parent / "chatroom"
MATRIX_ROOMS_CONFIG = Path(__file__).parent.parent / "matrix-credentials" / "matrix-rooms.json"
SYNC_STATE_FILE = Path(__file__).parent.parent / "matrix-credentials" / "bridge-sync-state.json"
HOMESERVER = os.getenv("MATRIX_HOMESERVER", "https://matrix.themultiverse.school")

# Bridge bot configuration (uses orchestrator by default)
BRIDGE_BOT_TOKEN = os.getenv("MATRIX_TOKEN_ORCHESTRATOR", "")
BRIDGE_BOT_USER_ID = "@agent-orchestrator:themultiverse.school"

# Load room mappings
def load_room_mappings() -> Dict[str, str]:
    """Load channel -> room_id mappings from JSON file."""
    try:
        with open(MATRIX_ROOMS_CONFIG, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Room mappings not found: {MATRIX_ROOMS_CONFIG}")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing room mappings: {e}")
        return {}

# Load sync state (tracks last processed message per channel)
def load_sync_state() -> Dict[str, dict]:
    """Load last sync position for each channel."""
    if SYNC_STATE_FILE.exists():
        try:
            with open(SYNC_STATE_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_sync_state(state: Dict[str, dict]):
    """Save sync state to disk."""
    SYNC_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SYNC_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

async def get_matrix_client() -> AsyncClient:
    """Create and configure Matrix client for bridge bot."""
    client = AsyncClient(HOMESERVER, BRIDGE_BOT_USER_ID)
    client.access_token = BRIDGE_BOT_TOKEN
    client.device_id = "BRIDGE_BOT_DEVICE"
    return client

def parse_chatroom_message(line: str) -> Optional[dict]:
    """
    Parse a chatroom message line.

    Format: [TIMESTAMP] [AGENT] [STATUS] MESSAGE

    Returns:
        dict with timestamp, agent, status, message or None if invalid
    """
    if not line.strip():
        return None

    try:
        # Example: [2025-10-31 16:00:00] [orchestrator] [STARTED] Starting coordination
        parts = line.split("] ", 3)
        if len(parts) < 4:
            return None

        timestamp = parts[0].replace("[", "").strip()
        agent = parts[1].replace("[", "").strip()
        status = parts[2].replace("[", "").strip()
        message = parts[3].strip()

        return {
            "timestamp": timestamp,
            "agent": agent,
            "status": status,
            "message": message,
            "raw": line
        }
    except Exception as e:
        print(f"⚠️ Error parsing line: {e}")
        return None

async def sync_chatroom_to_matrix(client: AsyncClient, channel: str, room_id: str, sync_state: dict):
    """
    Sync new messages from chatroom file to Matrix room.

    Args:
        client: Authenticated Matrix client
        channel: Channel name (e.g., 'coordination')
        room_id: Matrix room ID
        sync_state: Sync state dict for this channel
    """
    channel_file = CHATROOM_DIR / f"{channel}.txt"
    if not channel_file.exists():
        return

    # Get last processed line number
    last_line = sync_state.get(channel, {}).get("last_line", 0)

    # Read all lines
    with open(channel_file, 'r') as f:
        lines = f.readlines()

    # Process new lines only
    new_lines = lines[last_line:]
    if not new_lines:
        return  # Nothing new

    print(f"📤 Syncing {len(new_lines)} new messages from {channel} to Matrix")

    for i, line in enumerate(new_lines):
        msg = parse_chatroom_message(line)
        if not msg:
            continue

        # Format message for Matrix
        formatted_msg = f"[{msg['status']}] {msg['message']}"

        try:
            # Send to Matrix
            await client.room_send(
                room_id=room_id,
                message_type="m.room.message",
                content={
                    "msgtype": "m.text",
                    "body": formatted_msg,
                    "formatted_body": f"<strong>{msg['agent']}</strong>: {formatted_msg}",
                    "format": "org.matrix.custom.html",
                    # Add metadata for bridge identification
                    "uk.half-shot.bridge": {
                        "source": "chatroom-file",
                        "channel": channel,
                        "agent": msg['agent']
                    }
                }
            )
            print(f"  ✅ Posted: [{msg['agent']}] {msg['message'][:50]}...")

        except Exception as e:
            print(f"  ❌ Error posting message: {e}")

    # Update sync state
    sync_state[channel] = {
        "last_line": last_line + len(new_lines),
        "last_sync": datetime.now().isoformat()
    }

async def run_bridge(interval: int = 30, one_shot: bool = False):
    """
    Run the chatroom-Matrix bridge.

    Args:
        interval: Sync interval in seconds (default: 30)
        one_shot: Run once and exit (default: False)
    """
    if not BRIDGE_BOT_TOKEN:
        print("❌ Error: MATRIX_TOKEN_ORCHESTRATOR not set in ~/.superalignment-env")
        sys.exit(1)

    room_mappings = load_room_mappings()
    if not room_mappings:
        print("❌ Error: No room mappings configured")
        sys.exit(1)

    print(f"🌉 Starting Chatroom-Matrix Bridge")
    print(f"   Channels: {', '.join(room_mappings.keys())}")
    print(f"   Sync interval: {interval}s")
    print(f"   One-shot mode: {one_shot}")

    # Create Matrix client
    client = await get_matrix_client()

    try:
        # Initial sync to get room state
        await client.sync(timeout=30000, full_state=True)
        print("✅ Matrix client synced")

        while True:
            sync_state = load_sync_state()

            # Sync each channel
            for channel, room_id in room_mappings.items():
                try:
                    await sync_chatroom_to_matrix(client, channel, room_id, sync_state)
                except Exception as e:
                    print(f"❌ Error syncing {channel}: {e}")

            # Save sync state
            save_sync_state(sync_state)

            if one_shot:
                print("✅ One-shot sync complete")
                break

            # Wait before next sync
            print(f"⏱️  Waiting {interval}s until next sync...")
            await asyncio.sleep(interval)

    except KeyboardInterrupt:
        print("\n🛑 Bridge stopped by user")
    finally:
        await client.close()
        print("✅ Matrix client closed")

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Chatroom-Matrix Bridge")
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Sync interval in seconds (default: 30)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (default: continuous)"
    )

    args = parser.parse_args()

    asyncio.run(run_bridge(interval=args.interval, one_shot=args.once))

if __name__ == "__main__":
    main()
