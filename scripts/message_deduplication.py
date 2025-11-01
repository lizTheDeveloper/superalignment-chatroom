#!/usr/bin/env python3
"""
Message Deduplication System

Prevents double-spawning when messages flow through multiple systems:
- File-based chatroom (triggers.txt)
- Matrix rooms (real-time messaging)
- Chatroom-Matrix bridge (bidirectional sync)

Architecture:
- Generates deterministic message IDs from content + timestamp
- Tracks processed message IDs in shared state file
- Both trigger-monitor.py and bridge can check before processing
- Automatic cleanup of old message IDs (>24 hours)
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Set, Dict

# Shared state file location
STATE_DIR = Path(__file__).parent.parent / "matrix-credentials"
PROCESSED_MESSAGES_FILE = STATE_DIR / "processed-messages.json"

# Cleanup threshold (messages older than this are removed from state)
CLEANUP_THRESHOLD_HOURS = 24


def generate_message_id(
    content: str,
    sender: str,
    timestamp: Optional[str] = None,
    channel: Optional[str] = None
) -> str:
    """
    Generate deterministic message ID from content and metadata.

    Args:
        content: Message content
        sender: Agent/user who sent the message
        timestamp: Message timestamp (ISO format or human-readable)
        channel: Channel name (optional)

    Returns:
        SHA256 hash of normalized message data
    """
    # Normalize content (strip whitespace, lowercase for consistency)
    normalized_content = content.strip().lower()

    # Build hash input
    hash_input = f"{sender}:{normalized_content}"

    if timestamp:
        # Extract just date+hour to group messages sent within same hour
        # This prevents minor timestamp differences from creating different IDs
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            timestamp_key = dt.strftime("%Y-%m-%d %H")
        except (ValueError, AttributeError):
            # If timestamp parsing fails, use as-is
            timestamp_key = timestamp[:13] if len(timestamp) > 13 else timestamp

        hash_input += f":{timestamp_key}"

    if channel:
        hash_input += f":{channel}"

    # Generate SHA256 hash
    return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()[:16]


def load_processed_messages() -> Dict[str, dict]:
    """
    Load processed message IDs from state file.

    Returns:
        Dict mapping message_id -> {timestamp, source}
    """
    if not PROCESSED_MESSAGES_FILE.exists():
        return {}

    try:
        with open(PROCESSED_MESSAGES_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"⚠️  Warning: Corrupted deduplication state file, resetting")
        return {}


def save_processed_messages(messages: Dict[str, dict]):
    """Save processed message IDs to state file."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROCESSED_MESSAGES_FILE, 'w') as f:
        json.dump(messages, f, indent=2)


def is_message_processed(message_id: str) -> bool:
    """
    Check if message ID has already been processed.

    Args:
        message_id: Message ID to check

    Returns:
        True if message was already processed, False otherwise
    """
    messages = load_processed_messages()
    return message_id in messages


def mark_message_processed(
    message_id: str,
    source: str,
    metadata: Optional[dict] = None
):
    """
    Mark message ID as processed.

    Args:
        message_id: Message ID to mark
        source: Source that processed it (e.g., 'trigger-monitor', 'bridge')
        metadata: Optional additional metadata to store
    """
    messages = load_processed_messages()

    messages[message_id] = {
        "timestamp": datetime.now().isoformat(),
        "source": source,
        **(metadata or {})
    }

    # Cleanup old messages while we're here
    cleanup_old_messages(messages)

    save_processed_messages(messages)


def cleanup_old_messages(messages: Dict[str, dict]) -> int:
    """
    Remove messages older than CLEANUP_THRESHOLD_HOURS.

    Args:
        messages: Message dict to clean (modified in-place)

    Returns:
        Number of messages removed
    """
    threshold = datetime.now() - timedelta(hours=CLEANUP_THRESHOLD_HOURS)

    to_remove = []
    for msg_id, data in messages.items():
        try:
            msg_time = datetime.fromisoformat(data['timestamp'])
            if msg_time < threshold:
                to_remove.append(msg_id)
        except (ValueError, KeyError):
            # If timestamp is malformed, keep the message (safer)
            pass

    for msg_id in to_remove:
        del messages[msg_id]

    return len(to_remove)


def get_stats() -> dict:
    """
    Get deduplication statistics.

    Returns:
        Dict with processed count, cleanup info, etc.
    """
    messages = load_processed_messages()

    # Count by source
    sources = {}
    for data in messages.values():
        source = data.get('source', 'unknown')
        sources[source] = sources.get(source, 0) + 1

    # Find oldest message
    oldest = None
    if messages:
        timestamps = [
            datetime.fromisoformat(data['timestamp'])
            for data in messages.values()
            if 'timestamp' in data
        ]
        if timestamps:
            oldest = min(timestamps)

    return {
        "total_processed": len(messages),
        "by_source": sources,
        "oldest_message": oldest.isoformat() if oldest else None,
        "cleanup_threshold_hours": CLEANUP_THRESHOLD_HOURS
    }


if __name__ == "__main__":
    # CLI tool for inspecting deduplication state
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        stats = get_stats()
        print("=== Message Deduplication Stats ===")
        print(f"Total processed: {stats['total_processed']}")
        print(f"By source: {stats['by_source']}")
        print(f"Oldest message: {stats['oldest_message']}")
        print(f"Cleanup threshold: {stats['cleanup_threshold_hours']} hours")

    elif len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        messages = load_processed_messages()
        removed = cleanup_old_messages(messages)
        save_processed_messages(messages)
        print(f"✅ Cleaned up {removed} old messages")

    elif len(sys.argv) > 1 and sys.argv[1] == "reset":
        if PROCESSED_MESSAGES_FILE.exists():
            PROCESSED_MESSAGES_FILE.unlink()
            print("✅ Reset deduplication state")
        else:
            print("ℹ️  No state file to reset")

    else:
        print("Usage:")
        print("  python3 message_deduplication.py stats    - Show statistics")
        print("  python3 message_deduplication.py cleanup  - Clean old messages")
        print("  python3 message_deduplication.py reset    - Reset all state")
