#!/usr/bin/env python3
"""
MCP Chatroom Server (Python Implementation)

Provides MCP tools for multi-agent chatroom coordination.
File-based coordination layer for agents working on the simulation.

SECURITY NOTE: chatroom_leave tool intentionally removed (2025-10-31)
Agents should never leave channels - they are persistent coordination surfaces.
Leaving breaks multi-agent coordination and message routing.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List

from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Chatroom Server")

# Chatroom configuration - use working directory's .claude/chatroom
CHATROOM_ROOT = Path.cwd() / ".claude" / "chatroom"
CHANNELS_DIR = CHATROOM_ROOT / "channels"

# Ensure directories exist
CHANNELS_DIR.mkdir(parents=True, exist_ok=True)


def format_timestamp() -> str:
    """Format current timestamp for messages."""
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def get_channel_file(channel: str) -> Path:
    """Get path to channel file."""
    return CHANNELS_DIR / f"{channel}.md"


def get_lastread_file(channel: str, agent: str) -> Path:
    """Get path to agent's last-read marker file."""
    return CHATROOM_ROOT / f".{channel}_{agent}_lastread"


def get_active_file(channel: str) -> Path:
    """Get path to channel's active agents file."""
    return CHATROOM_ROOT / f".{channel}_active"


def count_lines(file_path: Path) -> int:
    """Count lines in a file."""
    try:
        return len(file_path.read_text().splitlines())
    except FileNotFoundError:
        return 0


def get_active_agents(channel: str) -> List[str]:
    """Get list of active agents in a channel."""
    active_file = get_active_file(channel)
    try:
        return [
            line.strip()
            for line in active_file.read_text().splitlines()
            if line.strip()
        ]
    except FileNotFoundError:
        return []


def add_active_agent(channel: str, agent: str) -> None:
    """Mark agent as active in channel."""
    active_file = get_active_file(channel)
    agents = get_active_agents(channel)

    # Remove if already exists (avoid duplicates)
    agents = [a for a in agents if a != agent]

    # Add agent
    agents.append(agent)

    active_file.write_text("\n".join(agents) + "\n")


@mcp.tool
async def chatroom_post(
    channel: str,
    agent: str,
    status: str,
    message: str
) -> str:
    """
    Post a message to a channel (append-only, no read).

    Args:
        channel: Channel name (e.g., "coordination", "research")
        agent: Agent username (choose once and reuse)
        status: Message status tag (ENTERED, STARTED, IN-PROGRESS, COMPLETED, BLOCKED, QUESTION, ALERT, HANDOFF, LEAVING)
        message: Message content

    Returns:
        Success confirmation
    """
    channel_file = get_channel_file(channel)

    # Create channel if doesn't exist
    if not channel_file.exists():
        channel_file.write_text(
            f"# {channel.capitalize()} Channel\n\n---\n"
        )

    # Append message
    message_block = (
        f"\n---\n"
        f"**{agent}** | {format_timestamp()} | [{status}]\n\n"
        f"{message}\n"
        f"---\n"
    )
    with channel_file.open("a") as f:
        f.write(message_block)

    return f"✓ Posted to {channel} [{status}]"


@mcp.tool
async def chatroom_read_new(
    channel: str,
    agent: str,
    limit: int = 50
) -> str:
    """
    Read new messages since last check (per-agent tracking).

    Args:
        channel: Channel name
        agent: Agent username
        limit: Maximum number of lines to return (default: 50, use 0 for unlimited)

    Returns:
        New messages or notification of no new messages
    """
    channel_file = get_channel_file(channel)

    if not channel_file.exists():
        return f"Channel {channel} does not exist"

    lastread_file = get_lastread_file(channel, agent)

    # Read last line number
    try:
        last_line = int(lastread_file.read_text().strip())
    except FileNotFoundError:
        last_line = 0

    # Read all lines
    all_lines = channel_file.read_text().splitlines()
    current_line = len(all_lines)

    if current_line <= last_line:
        return f"No new messages in {channel}"

    # Get new lines
    new_lines = all_lines[last_line:]

    # Apply limit if specified
    if limit > 0 and len(new_lines) > limit:
        new_lines = new_lines[:limit]

    # Update last read marker
    lastread_file.write_text(str(current_line))

    return (
        f"━━━ New messages in {channel} (for {agent}) ━━━\n"
        f"{chr(10).join(new_lines)}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


@mcp.tool
async def chatroom_enter(
    channel: str,
    agent: str,
    message: str = "Entered channel, now monitoring"
) -> str:
    """
    Enter a channel (mark as active, post entry message).

    Args:
        channel: Channel name
        agent: Agent username
        message: Optional entry message

    Returns:
        Success confirmation
    """
    # Add to active agents
    add_active_agent(channel, agent)

    # Post entry message
    channel_file = get_channel_file(channel)

    if not channel_file.exists():
        channel_file.write_text(
            f"# {channel.capitalize()} Channel\n\n---\n"
        )

    message_block = (
        f"\n---\n"
        f"**{agent}** | {format_timestamp()} | [ENTERED]\n\n"
        f"{message}\n"
        f"---\n"
    )
    with channel_file.open("a") as f:
        f.write(message_block)

    return f"✓ Entered {channel} as {agent}"


# NOTE: chatroom_leave tool intentionally removed (2025-10-31)
# Agents should NEVER leave channels - they are persistent coordination surfaces
# Leaving breaks multi-agent coordination and message routing
# If an agent needs to stop monitoring a channel, they simply stop reading it


@mcp.tool
async def chatroom_who_active(channel: str) -> str:
    """
    List active agents in a channel.

    Args:
        channel: Channel name

    Returns:
        List of active agents
    """
    agents = get_active_agents(channel)

    if not agents:
        return f"ℹ No agents currently active in {channel}"

    agent_list = "\n".join(f"  ● {a}" for a in agents)

    return (
        f"━━━ Active in {channel} ━━━\n"
        f"{agent_list}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


@mcp.tool
async def chatroom_list_channels() -> str:
    """
    List all available channels.

    Returns:
        List of channels with line counts and active agent counts
    """
    if not CHANNELS_DIR.exists():
        return "No channels found"

    channels = []
    for channel_file in CHANNELS_DIR.glob("*.md"):
        channel_name = channel_file.stem
        line_count = count_lines(channel_file)
        active_count = len(get_active_agents(channel_name))

        if active_count > 0:
            channels.append(f"  • {channel_name} ({line_count} lines, {active_count} active)")
        else:
            channels.append(f"  • {channel_name} ({line_count} lines)")

    if not channels:
        return "No channels found"

    return (
        "━━━ Available Channels ━━━\n"
        + "\n".join(channels)
        + "\n━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


@mcp.tool
async def chatroom_peek(channel: str, lines: int = 5) -> str:
    """
    Peek at last N lines (for context without marking as read).

    Args:
        channel: Channel name
        lines: Number of lines to show

    Returns:
        Last N lines from channel
    """
    channel_file = get_channel_file(channel)

    if not channel_file.exists():
        return f"Channel {channel} does not exist"

    all_lines = channel_file.read_text().splitlines()
    last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

    return (
        f"━━━ Last {lines} lines from {channel} ━━━\n"
        f"{chr(10).join(last_lines)}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


@mcp.tool
async def chatroom_create_channel(channel: str, description: str) -> str:
    """
    Create a new channel.

    Args:
        channel: Channel name
        description: Channel description

    Returns:
        Success confirmation or warning if exists
    """
    channel_file = get_channel_file(channel)

    if channel_file.exists():
        return f"⚠ Channel {channel} already exists"

    content = (
        f"# {channel.capitalize()} Channel\n\n"
        f"{description}\n\n"
        f"---\n"
    )
    channel_file.write_text(content)

    return f"✓ Created channel: {channel}"


@mcp.tool
async def chatroom_reset_lastread(
    channel: Optional[str] = None,
    agent: Optional[str] = None
) -> str:
    """
    Reset last-read marker (force re-read from beginning).

    Args:
        channel: Channel name (optional - omit to reset all)
        agent: Agent username (optional - omit to reset all agents for channel)

    Returns:
        Success confirmation
    """
    if not channel:
        # Clear all markers
        for marker_file in CHATROOM_ROOT.glob(".*_lastread"):
            marker_file.unlink()
        return "✓ Cleared all last-read markers"

    elif not agent:
        # Clear all agents' markers for channel
        for marker_file in CHATROOM_ROOT.glob(f".{channel}_*_lastread"):
            marker_file.unlink()
        return f"✓ Cleared all last-read markers for {channel}"

    else:
        # Clear specific agent's marker
        lastread_file = get_lastread_file(channel, agent)
        if lastread_file.exists():
            lastread_file.unlink()
        return f"✓ Cleared last-read marker for {agent} in {channel}"


if __name__ == "__main__":
    # Run as stdio MCP server
    mcp.run()
