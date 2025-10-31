#!/bin/bash

# Archive logs to Google Cloud Storage bucket
# Runs daily at 2am via cron on both Mac and cloud VM

# Get script directory and repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOGS_DIR="$REPO_DIR/logs"
BUCKET="gs://superalignment-chatroom-logs"
TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")
HOSTNAME=$(hostname)

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Archiving Logs to GCS: $TIMESTAMP ===${NC}"
echo "Hostname: $HOSTNAME"
echo "Logs directory: $LOGS_DIR"
echo "GCS bucket: $BUCKET"
echo ""

# Check if logs directory exists
if [ ! -d "$LOGS_DIR" ]; then
    echo -e "${YELLOW}⚠️  No logs directory found, nothing to archive${NC}"
    exit 0
fi

# Check if there are any log files
LOG_FILES=$(find "$LOGS_DIR" -type f \( -name "*.log" -o -name "*.log.gz" \) 2>/dev/null)
if [ -z "$LOG_FILES" ]; then
    echo -e "${YELLOW}⚠️  No log files found, nothing to archive${NC}"
    exit 0
fi

# Count log files
LOG_COUNT=$(echo "$LOG_FILES" | wc -l | xargs)
echo -e "${YELLOW}Found $LOG_COUNT log files to archive${NC}"

# Create archive directory in bucket with hostname and date
ARCHIVE_PATH="$BUCKET/$HOSTNAME/$TIMESTAMP"

# Archive each log file
ARCHIVED=0
FAILED=0

while IFS= read -r logfile; do
    if [ -f "$logfile" ]; then
        BASENAME=$(basename "$logfile")
        echo -e "${YELLOW}Uploading $BASENAME...${NC}"

        if gcloud storage cp "$logfile" "$ARCHIVE_PATH/$BASENAME"; then
            ((ARCHIVED++))
            echo -e "${GREEN}✓ Uploaded $BASENAME${NC}"
        else
            ((FAILED++))
            echo -e "${YELLOW}⚠️  Failed to upload $BASENAME${NC}"
        fi
    fi
done <<< "$LOG_FILES"

echo ""
echo -e "${BLUE}=== Archive Summary ===${NC}"
echo "Total log files: $LOG_COUNT"
echo "Successfully archived: $ARCHIVED"
echo "Failed: $FAILED"
echo "Archive location: $ARCHIVE_PATH"
echo ""

if [ $ARCHIVED -gt 0 ]; then
    echo -e "${GREEN}✓ Logs archived successfully${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  No logs were archived${NC}"
    exit 1
fi
