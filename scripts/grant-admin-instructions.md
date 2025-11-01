# How to Grant Admin Permissions in Matrix Rooms

## Issue
The automated script failed because the bot accounts don't have admin permissions in the rooms. You (as the room creator) need to grant admin permissions to yourself and potentially to the bots.

## Option 1: Using Element (Easiest)

### For Each Room:
1. Open the room in Element
2. Click the room name at the top → Room Settings
3. Click "Roles & Permissions"
4. Under "Privileged Users", find your user (@lizthedeveloper:themultiverse.school)
5. Set your power level to **100** (Admin)
6. Repeat for all 11 rooms:
   - coordination
   - research
   - research-critique
   - architecture
   - implementation
   - testing
   - documentation
   - roadmap
   - triggers
   - alerts
   - status

## Option 2: Using Matrix API (Manual cURL)

If you have your Matrix access token, you can use curl commands:

```bash
# Set your access token
export USER_TOKEN="your_access_token_here"
export HOMESERVER="https://matrix.themultiverse.school"
export USER_ID="@lizthedeveloper:themultiverse.school"

# For each room, run:
ROOM_ID="!G-uy0v5GZd9IUqFufg4KIt0ks6d7bNdwquD29SVC4-I"  # coordination

# Get current power levels
curl -X GET "${HOMESERVER}/_matrix/client/r0/rooms/${ROOM_ID}/state/m.room.power_levels" \
  -H "Authorization: Bearer ${USER_TOKEN}" | jq . > power_levels.json

# Edit power_levels.json to add:
# "users": {
#   "@lizthedeveloper:themultiverse.school": 100
# }

# Update power levels
curl -X PUT "${HOMESERVER}/_matrix/client/r0/rooms/${ROOM_ID}/state/m.room.power_levels" \
  -H "Authorization: Bearer ${USER_TOKEN}" \
  -H "Content-Type: application/json" \
  -d @power_levels.json
```

## Option 3: Automated Script (After Getting Your Token)

If you can provide your Matrix access token (stored securely in ~/.superalignment-env), I can create a script that uses your account to grant admin to yourself and the bots.

## Why the Bots Failed

The architect bot and other bots either:
1. Weren't invited to all rooms
2. Don't have admin permissions in the rooms

To fix this, you first need admin permissions yourself, then you can grant them to the bots using the scripts we have.

## Next Steps

1. **Easiest**: Use Element UI to grant yourself admin in all 11 rooms (takes ~5 minutes)
2. **After you have admin**: Run scripts to grant admin to bots if needed
3. **Verify**: Check that you can modify room settings

## Bot Admin Setup (After You Have Admin)

Once you have admin, you can grant admin to the bots:

```bash
# This will require modifying the grant-admin.py script to use YOUR credentials
# Or do it manually in Element for each bot in each room
```
