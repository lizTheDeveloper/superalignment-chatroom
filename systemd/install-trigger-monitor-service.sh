#!/bin/bash
# Install Trigger Monitor systemd service and timer

set -e

echo "🔧 Installing Trigger Monitor systemd service..."

# Check if running on VM or need to use gcloud
if [ -d "/home/lizthedeveloper_gmail_com" ]; then
    # Running on VM
    SUDO_CMD="sudo"
    SCRIPT_DIR="/home/lizthedeveloper_gmail_com/src/superalignment-chatroom/systemd"
else
    # Running on local machine, use gcloud
    echo "❌ Error: This script must be run on the VM"
    echo "Use: gcloud compute ssh claude-workspace --zone=europe-west10-a --command 'bash /home/lizthedeveloper_gmail_com/src/superalignment-chatroom/systemd/install-trigger-monitor-service.sh'"
    exit 1
fi

# Copy service and timer files to systemd directory
echo "📋 Copying service files to /etc/systemd/system/..."
$SUDO_CMD cp ${SCRIPT_DIR}/trigger-monitor.service /etc/systemd/system/
$SUDO_CMD cp ${SCRIPT_DIR}/trigger-monitor.timer /etc/systemd/system/

# Reload systemd daemon
echo "🔄 Reloading systemd daemon..."
$SUDO_CMD systemctl daemon-reload

# Enable the timer
echo "✅ Enabling trigger-monitor.timer..."
$SUDO_CMD systemctl enable trigger-monitor.timer

# Start the timer
echo "🚀 Starting trigger-monitor.timer..."
$SUDO_CMD systemctl start trigger-monitor.timer

# Show status
echo ""
echo "═══════════════════════════════════════"
echo "📊 Service Status"
echo "═══════════════════════════════════════"
$SUDO_CMD systemctl status trigger-monitor.timer --no-pager || true

echo ""
echo "═══════════════════════════════════════"
echo "⏱️  Next Scheduled Runs"
echo "═══════════════════════════════════════"
$SUDO_CMD systemctl list-timers trigger-monitor.timer --no-pager

echo ""
echo "✅ Installation complete!"
echo ""
echo "📝 Useful commands:"
echo "  Check status:  sudo systemctl status trigger-monitor.timer"
echo "  View logs:     sudo journalctl -u trigger-monitor.service -f"
echo "  Stop timer:    sudo systemctl stop trigger-monitor.timer"
echo "  Disable timer: sudo systemctl disable trigger-monitor.timer"
