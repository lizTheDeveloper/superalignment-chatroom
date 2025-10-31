#!/bin/bash

# Auto-sync script for superalignment-chatroom
# Commits and pushes changes every 5 minutes (run via cron or while loop)
#
# Usage:
#   bash scripts/auto-sync.sh           # Single sync
#   bash scripts/auto-sync.sh --loop    # Continuous (every 5 min)

REPO_DIR="/Users/annhoward/src/superalignment-chatroom"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
LOOP_MODE=false

# Parse arguments
if [[ "$1" == "--loop" ]]; then
    LOOP_MODE=true
fi

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

sync_repo() {
    cd "$REPO_DIR" || exit 1

    echo -e "${BLUE}=== Chatroom Auto-Sync: $TIMESTAMP ===${NC}"

    # Pull latest changes first (in case other VMs pushed)
    echo -e "${YELLOW}Pulling latest changes...${NC}"
    git pull --rebase --autostash

    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}⚠️  Pull had conflicts, resolving...${NC}"
        # For chatroom files, prefer remote (other VMs' updates)
        git checkout --theirs chatroom/
        git add chatroom/
        git rebase --continue
    fi

    # Check if there are changes to commit
    if [[ -z $(git status --porcelain) ]]; then
        echo -e "${GREEN}✓ No changes to sync${NC}"
        return 0
    fi

    # Add all changes
    git add .

    # Count changes
    CHANGED_FILES=$(git diff --cached --name-only | wc -l | xargs)

    # Create commit message
    COMMIT_MSG="Auto-sync: ${TIMESTAMP}

Changes:
$(git diff --cached --stat)

Modified by: $(hostname)"

    # Commit
    echo -e "${YELLOW}Committing $CHANGED_FILES files...${NC}"
    git commit -m "$COMMIT_MSG"

    # Push
    echo -e "${YELLOW}Pushing to remote...${NC}"
    git push

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Successfully synced $CHANGED_FILES files${NC}"
    else
        echo -e "${YELLOW}⚠️  Push failed, will retry next cycle${NC}"
        return 1
    fi

    echo ""
}

if [ "$LOOP_MODE" = true ]; then
    echo -e "${BLUE}Starting auto-sync loop (every 5 minutes)${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo ""

    while true; do
        sync_repo
        sleep 300  # 5 minutes
    done
else
    # Single sync
    sync_repo
fi
