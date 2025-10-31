#!/usr/bin/env python3
"""Quick test script to post a message to Matrix."""

import os
import sys
import asyncio
from pathlib import Path
from nio import AsyncClient
from dotenv import load_dotenv

# Load environment
env_path = Path.home() / ".superalignment-env"
if env_path.exists():
    load_dotenv(env_path)

async def post_test_message():
    """Post a test message to coordination room."""
    HOMESERVER = "https://matrix.themultiverse.school"
    TOKEN = os.getenv("MATRIX_TOKEN_ORCHESTRATOR", "")
    USER_ID = "@agent-orchestrator:themultiverse.school"
    ROOM_ID = "!G-uy0v5GZd9IUqFufg4KIt0ks6d7bNdwquD29SVC4-I"  # coordination

    if not TOKEN:
        print("❌ MATRIX_TOKEN_ORCHESTRATOR not set")
        return

    # Create client
    client = AsyncClient(HOMESERVER, USER_ID)
    client.access_token = TOKEN
    client.device_id = "TEST_DEVICE"

    try:
        # Post message
        response = await client.room_send(
            room_id=ROOM_ID,
            message_type="m.room.message",
            content={
                "msgtype": "m.text",
                "body": "🚀 Test message from Matrix FastMCP server - integration working!",
                "formatted_body": "<strong>orchestrator</strong>: 🚀 Test message from Matrix FastMCP server - integration working!",
                "format": "org.matrix.custom.html"
            }
        )

        print(f"✅ Message posted! Event ID: {response.event_id}")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(post_test_message())
