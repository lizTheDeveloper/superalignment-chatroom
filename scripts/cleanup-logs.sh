#!/bin/bash

# Clean up logs from local repo after archival to GCS
# Runs daily at 2am via cron on both Mac and cloud VM
# Should be run AFTER archive-logs-to-gcs.sh

# Get script directory and repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOGS_DIR="$REPO_DIR/logs"
TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=== Cleaning Up Logs: $TIMESTAMP ===${NC}"
echo "Logs directory: $LOGS_DIR"
echo ""

# Check if logs directory exists
if [ ! -d "$LOGS_DIR" ]; then
    echo -e "${YELLOW}⚠️  No logs directory found, nothing to clean${NC}"
    exit 0
fi

# Find all log files
LOG_FILES=$(find "$LOGS_DIR" -type f \( -name "*.log" -o -name "*.log.gz" \) 2>/dev/null)
if [ -z "$LOG_FILES" ]; then
    echo -e "${YELLOW}⚠️  No log files found, nothing to clean${NC}"
    exit 0
fi

# Count log files
LOG_COUNT=$(echo "$LOG_FILES" | wc -l | xargs)
echo -e "${YELLOW}Found $LOG_COUNT log files to remove${NC}"

# Calculate total size before cleanup
TOTAL_SIZE=$(du -sh "$LOGS_DIR" 2>/dev/null | cut -f1)
echo "Current logs directory size: $TOTAL_SIZE"
echo ""

# Remove each log file
REMOVED=0
FAILED=0

while IFS= read -r logfile; do
    if [ -f "$logfile" ]; then
        BASENAME=$(basename "$logfile")

        if rm "$logfile"; then
            ((REMOVED++))
            echo -e "${GREEN}✓ Removed $BASENAME${NC}"
        else
            ((FAILED++))
            echo -e "${RED}❌ Failed to remove $BASENAME${NC}"
        fi
    fi
done <<< "$LOG_FILES"

# Calculate size after cleanup
FINAL_SIZE=$(du -sh "$LOGS_DIR" 2>/dev/null | cut -f1)

echo ""
echo -e "${BLUE}=== Cleanup Summary ===${NC}"
echo "Total log files: $LOG_COUNT"
echo "Successfully removed: $REMOVED"
echo "Failed: $FAILED"
echo "Size before: $TOTAL_SIZE"
echo "Size after: $FINAL_SIZE"
echo ""

if [ $REMOVED -gt 0 ]; then
    echo -e "${GREEN}✓ Logs cleaned up successfully${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  No logs were removed${NC}"
    exit 1
fi
