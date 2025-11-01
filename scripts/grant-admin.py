#!/usr/bin/env python3
"""
Grant Admin Permissions to User in All Matrix Rooms

Uses the architect bot (which has admin in all rooms) to set power level to 100 for specified user.
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from nio import AsyncClient, RoomPutStateError

# Load environment variables
env_path = Path.home() / ".superalignment-env"
if not env_path.exists():
    print(f"❌ Error: {env_path} not found")
    sys.exit(1)

load_dotenv(env_path)

# Configuration
HOMESERVER = os.getenv("MATRIX_HOMESERVER", "https://matrix.themultiverse.school")
ARCHITECT_TOKEN = os.getenv("MATRIX_TOKEN_ARCHITECT", "")

# Load room mappings
rooms_config_path = Path.home() / "src/superalignment-chatroom/matrix-credentials/matrix-rooms.json"
if not rooms_config_path.exists():
    print(f"❌ Error: {rooms_config_path} not found")
    sys.exit(1)

with open(rooms_config_path, 'r') as f:
    ROOM_MAPPINGS = json.load(f)

async def grant_admin(user_id: str):
    """Grant admin power level to user in all rooms."""

    if not ARCHITECT_TOKEN:
        print("❌ Error: MATRIX_TOKEN_ARCHITECT not found in ~/.superalignment-env")
        return False

    # Create client as architect (has admin in all rooms)
    client = AsyncClient(HOMESERVER, "@architect:themultiverse.school")
    client.access_token = ARCHITECT_TOKEN

    try:
        # Sync to get current state
        print("🔄 Syncing Matrix client...")
        await client.sync(timeout=3000)

        success_count = 0
        fail_count = 0

        for channel_name, room_id in ROOM_MAPPINGS.items():
            print(f"\n📝 Processing {channel_name} ({room_id})...")

            try:
                # Get current power levels
                power_levels_event = await client.room_get_state_event(
                    room_id,
                    "m.room.power_levels"
                )

                if isinstance(power_levels_event, RoomPutStateError):
                    print(f"  ❌ Failed to get power levels: {power_levels_event.message}")
                    fail_count += 1
                    continue

                # Modify power levels to add user as admin (100)
                power_levels = power_levels_event.content
                if "users" not in power_levels:
                    power_levels["users"] = {}

                power_levels["users"][user_id] = 100

                # Update power levels
                response = await client.room_put_state(
                    room_id,
                    "m.room.power_levels",
                    power_levels
                )

                if isinstance(response, RoomPutStateError):
                    print(f"  ❌ Failed to update power levels: {response.message}")
                    fail_count += 1
                else:
                    print(f"  ✅ Granted admin to {user_id}")
                    success_count += 1

            except Exception as e:
                print(f"  ❌ Error: {e}")
                fail_count += 1

        print(f"\n{'='*50}")
        print(f"✅ Success: {success_count}/{len(ROOM_MAPPINGS)} rooms")
        print(f"❌ Failed: {fail_count}/{len(ROOM_MAPPINGS)} rooms")

        return fail_count == 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        await client.close()

async def main():
    if len(sys.argv) != 2:
        print("Usage: grant-admin.py @user:server.com")
        print("Example: grant-admin.py @lizthedeveloper:themultiverse.school")
        sys.exit(1)

    user_id = sys.argv[1]

    if not user_id.startswith("@"):
        print("❌ Error: User ID must start with @")
        sys.exit(1)

    print(f"🔧 Granting admin permissions to {user_id} in all Matrix rooms...")
    print(f"   Using architect bot for admin operations")
    print(f"   Rooms: {len(ROOM_MAPPINGS)}")

    success = await grant_admin(user_id)

    if success:
        print("\n✅ All permissions granted successfully!")
        sys.exit(0)
    else:
        print("\n⚠️ Some permissions failed to update")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
