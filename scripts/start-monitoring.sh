#!/bin/bash
#
# Start all three monitoring processes for Matrix ↔ Chatroom ↔ Agent flow
#
# Usage:
#   ./scripts/start-monitoring.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHATROOM_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$CHATROOM_DIR/logs"

# Create logs directory if needed
mkdir -p "$LOG_DIR"

# Kill any existing processes first
echo "🛑 Stopping any existing monitoring processes..."
pkill -f 'matrix-listener.py' || true
pkill -f 'trigger-monitor.py' || true
pkill -f 'chatroom-matrix-bridge.py' || true
sleep 1

# Clear old logs
> "$LOG_DIR/matrix-listener.log"
> "$LOG_DIR/trigger-monitor.log"
> "$LOG_DIR/chatroom-matrix-bridge.log"

echo "🚀 Starting monitoring processes..."
echo ""

# Start matrix-listener (listens to Matrix rooms, writes to triggers.txt)
cd "$CHATROOM_DIR"
nohup python3 scripts/matrix-listener.py --interval 30 \
  > "$LOG_DIR/matrix-listener.log" 2>&1 &
LISTENER_PID=$!
echo "✅ matrix-listener started (PID: $LISTENER_PID)"
echo "   Listens to Matrix rooms, detects @mentions"
echo "   Writes to: chatroom/triggers.txt"
echo "   Log: logs/matrix-listener.log"
echo ""

# Start trigger-monitor (reads triggers.txt, spawns agents)
nohup python3 scripts/trigger-monitor.py --interval 300 \
  > "$LOG_DIR/trigger-monitor.log" 2>&1 &
MONITOR_PID=$!
echo "✅ trigger-monitor started (PID: $MONITOR_PID)"
echo "   Reads from: chatroom/triggers.txt"
echo "   Spawns agents based on @mentions"
echo "   Log: logs/trigger-monitor.log"
echo ""

# Start chatroom-matrix-bridge (syncs chatroom files → Matrix)
nohup python3 scripts/chatroom-matrix-bridge.py --interval 30 \
  > "$LOG_DIR/chatroom-matrix-bridge.log" 2>&1 &
BRIDGE_PID=$!
echo "✅ chatroom-matrix-bridge started (PID: $BRIDGE_PID)"
echo "   Syncs chatroom/*.txt → Matrix rooms"
echo "   Log: logs/chatroom-matrix-bridge.log"
echo ""

echo "⏳ Waiting 5 seconds for startup..."
sleep 5

echo ""
echo "📋 Process Status:"
if ps -p $LISTENER_PID > /dev/null; then
    echo "  ✅ matrix-listener running (PID: $LISTENER_PID)"
else
    echo "  ❌ matrix-listener NOT running (check logs/matrix-listener.log)"
fi

if ps -p $MONITOR_PID > /dev/null; then
    echo "  ✅ trigger-monitor running (PID: $MONITOR_PID)"
else
    echo "  ❌ trigger-monitor NOT running (check logs/trigger-monitor.log)"
fi

if ps -p $BRIDGE_PID > /dev/null; then
    echo "  ✅ chatroom-matrix-bridge running (PID: $BRIDGE_PID)"
else
    echo "  ❌ chatroom-matrix-bridge NOT running (check logs/chatroom-matrix-bridge.log)"
fi

echo ""
echo "📊 Check logs:"
echo "   tail -f logs/matrix-listener.log"
echo "   tail -f logs/trigger-monitor.log"
echo "   tail -f logs/chatroom-matrix-bridge.log"
echo ""
echo "🛑 Stop all:"
echo "   pkill -f 'matrix-listener.py|trigger-monitor.py|chatroom-matrix-bridge.py'"
echo ""
echo "✅ Monitoring system started!"
