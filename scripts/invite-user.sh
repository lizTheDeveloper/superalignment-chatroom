#!/usr/bin/env bash

# Invite a user to all Matrix rooms

set -e

HOMESERVER="https://matrix.themultiverse.school"
CREDS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/matrix-credentials"

# Load credentials
source "$CREDS_DIR/.env"

# Load room mappings
ROOMS_JSON="$CREDS_DIR/matrix-rooms.json"

# Use orchestrator token
TOKEN="$MATRIX_TOKEN_ORCHESTRATOR"

# User to invite (can be passed as argument)
USER_ID="${1:-@lizthedeveloper:themultiverse.school}"

echo "Inviting $USER_ID to all rooms..."
echo ""

# Invite to all rooms
for room in coordination research "research-critique" architecture implementation testing documentation roadmap triggers alerts status; do
    ROOM_ID=$(jq -r ".\"$room\"" "$ROOMS_JSON")
    
    if [ "$ROOM_ID" != "null" ] && [ -n "$ROOM_ID" ]; then
        echo "Inviting to: $room ($ROOM_ID)"
        
        RESULT=$(curl -s -X POST "${HOMESERVER}/_matrix/client/r0/rooms/${ROOM_ID}/invite" \
            -H "Authorization: Bearer ${TOKEN}" \
            -H "Content-Type: application/json" \
            -d "{\"user_id\": \"$USER_ID\"}")
        
        if echo "$RESULT" | grep -q "error"; then
            ERROR=$(echo "$RESULT" | jq -r '.error // .errcode')
            echo "  ⚠️  $ERROR"
        else
            echo "  ✓ Invited"
        fi
    fi
done

echo ""
echo "Invitation complete!"
echo "User $USER_ID has been invited to all rooms."
