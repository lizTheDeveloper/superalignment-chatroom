#!/usr/bin/env python3
"""
Matrix FastMCP Server
A stdio-based MCP server for Matrix integration with Claude Code.
Uses matrix-nio for Matrix client functionality.
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

from fastmcp import FastMCP
from nio import AsyncClient, RoomSendResponse, RoomMessageText, LoginResponse, RoomInviteResponse
from dotenv import load_dotenv

# Load environment variables from ~/.superalignment-env
env_path = Path.home() / ".superalignment-env"
if env_path.exists():
    load_dotenv(env_path)

# Load room mappings
ROOMS_CONFIG_PATH = os.getenv(
    "MATRIX_ROOMS_CONFIG",
    str(Path.home() / "src/superalignment-chatroom/matrix-credentials/matrix-rooms.json")
)

# Matrix configuration
HOMESERVER = os.getenv("MATRIX_HOMESERVER", "https://matrix.themultiverse.school")

# Bot token mapping
BOT_TOKENS = {
    "aetherix": os.getenv("MATRIX_TOKEN_AETHERIX", ""),
    "orchestrator": os.getenv("MATRIX_TOKEN_ORCHESTRATOR", ""),
    "sylvia": os.getenv("MATRIX_TOKEN_SYLVIA", ""),
    "roy": os.getenv("MATRIX_TOKEN_ROY", ""),
    "cynthia": os.getenv("MATRIX_TOKEN_CYNTHIA", ""),
    "moss": os.getenv("MATRIX_TOKEN_MOSS", ""),
    "tessa": os.getenv("MATRIX_TOKEN_TESSA", ""),
    "historian": os.getenv("MATRIX_TOKEN_HISTORIAN", ""),
    "architect": os.getenv("MATRIX_TOKEN_ARCHITECT", ""),
    "ray": os.getenv("MATRIX_TOKEN_RAY", ""),
    "monitor": os.getenv("MATRIX_TOKEN_MONITOR", ""),
}

# Load room mappings from JSON
def load_room_mappings() -> Dict[str, str]:
    """Load channel -> room_id mappings from JSON file."""
    try:
        with open(ROOMS_CONFIG_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing room mappings: {e}", file=sys.stderr)
        return {}

ROOM_MAPPINGS = load_room_mappings()

# Initialize FastMCP server
mcp = FastMCP("Matrix Server")

async def get_matrix_client(agent_name: str) -> Optional[AsyncClient]:
    """
    Create and login a Matrix client for the given agent.

    Args:
        agent_name: Agent name (e.g., 'orchestrator', 'sylvia', 'roy')

    Returns:
        Authenticated AsyncClient or None if token missing
    """
    token = BOT_TOKENS.get(agent_name.lower())
    if not token:
        return None

    # Create client with agent's Matrix ID
    user_id = f"@agent-{agent_name.lower()}:themultiverse.school"
    client = AsyncClient(HOMESERVER, user_id)

    # Set access token and device_id directly (we already have them)
    client.access_token = token
    # Device ID can be derived from agent name for consistency
    client.device_id = f"{agent_name.upper()}_DEVICE"

    return client

@mcp.tool
async def matrix_post_message(
    channel: str,
    agent: str,
    message: str,
    status: Optional[str] = None
) -> str:
    """
    Post a message to a Matrix room.

    Args:
        channel: Channel name (e.g., 'coordination', 'research')
        agent: Agent username posting the message
        message: Message content
        status: Optional status tag

    Returns:
        Success message with event_id or error message
    """
    # Get room ID from channel name
    room_id = ROOM_MAPPINGS.get(channel)
    if not room_id:
        return f"Error: Unknown channel '{channel}'. Available channels: {', '.join(ROOM_MAPPINGS.keys())}"

    # Get Matrix client for agent
    client = await get_matrix_client(agent)
    if not client:
        return f"Error: No Matrix token configured for agent '{agent}'"

    try:
        # Format message with status if provided
        formatted_message = f"[{status}] {message}" if status else message

        # Send message
        response = await client.room_send(
            room_id=room_id,
            message_type="m.room.message",
            content={
                "msgtype": "m.text",
                "body": formatted_message,
                "formatted_body": f"<strong>{agent}</strong>: {formatted_message}",
                "format": "org.matrix.custom.html"
            }
        )

        if isinstance(response, RoomSendResponse):
            return f"✅ Message posted to {channel} (event_id: {response.event_id})"
        else:
            return f"❌ Error posting message: {response}"

    except Exception as e:
        return f"❌ Error: {str(e)}"

    finally:
        await client.close()

@mcp.tool
async def matrix_invite_user(
    channel: str,
    agent: str,
    user_id: str
) -> str:
    """
    Invite a user to a Matrix room.

    Args:
        channel: Channel name (e.g., 'coordination', 'research')
        agent: Agent username performing the invitation (must have invite permissions)
        user_id: Matrix user ID to invite (e.g., '@user:domain.com')

    Returns:
        Success or error message
    """
    # Get room ID from channel name
    room_id = ROOM_MAPPINGS.get(channel)
    if not room_id:
        return f"Error: Unknown channel '{channel}'. Available channels: {', '.join(ROOM_MAPPINGS.keys())}"

    # Get Matrix client for agent
    client = await get_matrix_client(agent)
    if not client:
        return f"Error: No Matrix token configured for agent '{agent}'"

    try:
        # Invite user
        response = await client.room_invite(room_id, user_id)

        if isinstance(response, RoomInviteResponse):
            return f"✅ Invited {user_id} to {channel}"
        else:
            return f"❌ Error inviting user: {response}"

    except Exception as e:
        return f"❌ Error: {str(e)}"

    finally:
        await client.close()

@mcp.tool
async def matrix_list_rooms(agent: str = "orchestrator") -> str:
    """
    List all configured Matrix rooms and their mappings.

    Args:
        agent: Agent username to use for authentication (default: orchestrator)

    Returns:
        Formatted list of channel -> room_id mappings
    """
    if not ROOM_MAPPINGS:
        return "No room mappings configured. Check MATRIX_ROOMS_CONFIG path."

    result = ["📋 **Configured Matrix Rooms**\n"]
    for channel, room_id in ROOM_MAPPINGS.items():
        result.append(f"  • {channel}: {room_id}")

    return "\n".join(result)

@mcp.tool
async def matrix_check_membership(
    channel: str,
    user_id: str,
    agent: str = "orchestrator"
) -> str:
    """
    Check if a user is a member of a Matrix room.

    Args:
        channel: Channel name (e.g., 'coordination', 'research')
        user_id: Matrix user ID to check (e.g., '@user:domain.com')
        agent: Agent username to use for authentication

    Returns:
        Membership status message
    """
    # Get room ID from channel name
    room_id = ROOM_MAPPINGS.get(channel)
    if not room_id:
        return f"Error: Unknown channel '{channel}'"

    # Get Matrix client for agent
    client = await get_matrix_client(agent)
    if not client:
        return f"Error: No Matrix token configured for agent '{agent}'"

    try:
        # Sync to get room state
        await client.sync(timeout=30000, full_state=True)

        # Get room
        room = client.rooms.get(room_id)
        if not room:
            return f"❌ Room {channel} ({room_id}) not found in sync"

        # Check if user is in room
        is_member = user_id in room.users

        if is_member:
            return f"✅ {user_id} is a member of {channel}"
        else:
            return f"❌ {user_id} is NOT a member of {channel}"

    except Exception as e:
        return f"❌ Error: {str(e)}"

    finally:
        await client.close()

@mcp.tool
async def matrix_get_notifications(
    agent: str,
    channels: Optional[list[str]] = None
) -> str:
    """
    Get unread notification count for an agent across Matrix rooms.

    Args:
        agent: Agent username to check notifications for
        channels: Optional list of channel names to check (default: all configured channels)

    Returns:
        Formatted notification summary
    """
    # Get Matrix client for agent
    client = await get_matrix_client(agent)
    if not client:
        return f"Error: No Matrix token configured for agent '{agent}'"

    try:
        # Sync to get latest room state
        sync_response = await client.sync(timeout=30000, full_state=False)

        # Determine which channels to check
        channels_to_check = channels if channels else list(ROOM_MAPPINGS.keys())

        result = [f"📬 **Notifications for {agent}**\n"]
        total_notifications = 0

        for channel in channels_to_check:
            room_id = ROOM_MAPPINGS.get(channel)
            if not room_id:
                continue

            room = client.rooms.get(room_id)
            if not room:
                continue

            # Get notification count (unread messages)
            unread_count = room.unread_notifications or 0
            highlight_count = room.unread_highlights or 0

            if unread_count > 0 or highlight_count > 0:
                result.append(
                    f"  • **{channel}**: {unread_count} unread"
                    + (f" ({highlight_count} highlights)" if highlight_count > 0 else "")
                )
                total_notifications += unread_count

        if total_notifications == 0:
            result.append("  ✅ No unread notifications")
        else:
            result.insert(1, f"**Total**: {total_notifications} unread messages\n")

        return "\n".join(result)

    except Exception as e:
        return f"❌ Error: {str(e)}"

    finally:
        await client.close()

@mcp.tool
async def matrix_create_room(
    channel_name: str,
    agent: str,
    topic: Optional[str] = None,
    invite_user_id: Optional[str] = None,
    is_private: bool = True
) -> str:
    """
    Create a new Matrix room (RESTRICTED: Only 'architect' agent can create rooms).

    Args:
        channel_name: Friendly name for the channel
        agent: Agent username (must be 'architect')
        topic: Optional room topic/description
        invite_user_id: User ID to invite immediately (e.g., '@user:domain.com')
        is_private: Whether room is private (default: True)

    Returns:
        Success message with room_id or error
    """
    # SECURITY: Only architect can create rooms
    if agent.lower() != "architect":
        return f"❌ Error: Only 'architect' agent can create rooms (you are '{agent}')"

    # Get Matrix client for architect
    client = await get_matrix_client(agent)
    if not client:
        return f"Error: No Matrix token configured for agent '{agent}'"

    try:
        # Create room
        from nio import RoomCreateResponse, RoomPreset

        response = await client.room_create(
            name=channel_name,
            topic=topic,
            invite=[invite_user_id] if invite_user_id else [],
            visibility="private" if is_private else "public",
            preset=RoomPreset.private_chat if is_private else RoomPreset.public_chat
        )

        if isinstance(response, RoomCreateResponse):
            room_id = response.room_id
            # Save to room mappings file
            ROOM_MAPPINGS[channel_name] = room_id
            with open(ROOMS_CONFIG_PATH, 'w') as f:
                json.dump(ROOM_MAPPINGS, f, indent=2)

            invite_msg = f" (invited {invite_user_id})" if invite_user_id else ""
            return f"✅ Created room '{channel_name}'\n  Room ID: {room_id}{invite_msg}\n  Saved to {ROOMS_CONFIG_PATH}"
        else:
            return f"❌ Error creating room: {response}"

    except Exception as e:
        return f"❌ Error: {str(e)}"

    finally:
        await client.close()

if __name__ == "__main__":
    # Run as stdio MCP server
    mcp.run()
