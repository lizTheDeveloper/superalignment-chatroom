#!/bin/bash

# Install auto-sync as a background service
# Runs every 5 minutes via cron

# Get script directory and repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SCRIPT_PATH="$REPO_DIR/scripts/auto-sync.sh"
LOG_DIR="$REPO_DIR/logs"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Installing Auto-Sync ===${NC}"

# Create logs directory
mkdir -p "$LOG_DIR"

# Check if already installed
if crontab -l 2>/dev/null | grep -q "superalignment-chatroom/scripts/auto-sync.sh"; then
    echo -e "${YELLOW}⚠️  Auto-sync already installed in crontab${NC}"
    echo ""
    echo "Current cron entry:"
    crontab -l | grep "superalignment-chatroom"
    echo ""
    read -p "Remove and reinstall? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi

    # Remove existing entry
    crontab -l | grep -v "superalignment-chatroom" | crontab -
fi

# Add cron job (every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * bash $SCRIPT_PATH >> $LOG_DIR/auto-sync.log 2>&1") | crontab -

echo -e "${GREEN}✓ Auto-sync installed!${NC}"
echo ""
echo "Configuration:"
echo "  Frequency: Every 5 minutes"
echo "  Script: $SCRIPT_PATH"
echo "  Logs: $LOG_DIR/auto-sync.log"
echo ""
echo "To view logs:"
echo "  tail -f $LOG_DIR/auto-sync.log"
echo ""
echo "To uninstall:"
echo "  crontab -e  # Remove the line with 'superalignment-chatroom'"
echo ""
echo -e "${BLUE}Testing initial sync...${NC}"
bash "$SCRIPT_PATH"
