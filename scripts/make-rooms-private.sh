#!/usr/bin/env bash

# Make Matrix rooms private (not visible in directory)

set -e

HOMESERVER="https://matrix.themultiverse.school"
CREDS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/matrix-credentials"

# Load credentials
source "$CREDS_DIR/.env"

# Load room mappings
ROOMS_JSON="$CREDS_DIR/matrix-rooms.json"

# Use orchestrator token
TOKEN="$MATRIX_TOKEN_ORCHESTRATOR"

echo "Making rooms private..."
echo ""

# Get room IDs from JSON - use quotes for keys with hyphens
for room in coordination research "research-critique" architecture implementation testing documentation roadmap triggers alerts status; do
    ROOM_ID=$(jq -r ".\"$room\"" "$ROOMS_JSON")
    
    if [ "$ROOM_ID" != "null" ] && [ -n "$ROOM_ID" ]; then
        echo "Processing: $room ($ROOM_ID)"
        
        # Set join rules to invite-only
        curl -s -X PUT "${HOMESERVER}/_matrix/client/r0/rooms/${ROOM_ID}/state/m.room.join_rules" \
            -H "Authorization: Bearer ${TOKEN}" \
            -H "Content-Type: application/json" \
            -d '{"join_rule": "invite"}' > /dev/null
        
        # Set history visibility to invited
        curl -s -X PUT "${HOMESERVER}/_matrix/client/r0/rooms/${ROOM_ID}/state/m.room.history_visibility" \
            -H "Authorization: Bearer ${TOKEN}" \
            -H "Content-Type: application/json" \
            -d '{"history_visibility": "invited"}' > /dev/null
        
        # Remove from directory
        curl -s -X PUT "${HOMESERVER}/_matrix/client/r0/directory/list/room/${ROOM_ID}" \
            -H "Authorization: Bearer ${TOKEN}" \
            -H "Content-Type: application/json" \
            -d '{"visibility": "private"}' > /dev/null
        
        echo "  ✓ Made private (invite-only, not in directory)"
    fi
done

echo ""
echo "All rooms are now private!"
echo "- Join rules: invite-only"
echo "- History: visible only to invited members"
echo "- Directory: not listed"
