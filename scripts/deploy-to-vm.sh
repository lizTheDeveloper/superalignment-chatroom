#!/bin/bash
# Deploy trigger monitor and related files to GCloud VM

set -e

VM_NAME="claude-workspace"
VM_ZONE="europe-west10-a"
REMOTE_DIR="~/src/superalignment-chatroom"

echo "🚀 Deploying to ${VM_NAME}..."

# First, commit and push changes to git (so VM can pull them)
echo "📦 Committing changes to git..."
cd "$(dirname "$0")/.."

git add scripts/trigger-monitor.py \
        scripts/test-post-message.py \
        scripts/test-matrix-post.sh \
        systemd/trigger-monitor.service \
        TRIGGER_MONITOR.md \
        QUICK_START_TRIGGERS.md \
        chatroom/triggers.txt \
        .claude/agents/mcp-configs/*.json

git commit -m "feat: Add trigger monitor with agent sequencing and Haiku delivery

- Trigger monitor watches chatroom/triggers.txt for @agent mentions
- Sequences agent launches with staggered delays (sylvia 0s, roy 10s, etc.)
- Uses Haiku for deterministic message delivery
- Per-agent MCP configs (matrix.mcp.json, minimal.mcp.json, full.mcp.json)
- Headless skip-permissions mode for autonomous operation
- Systemd service file for daemon mode
- Comprehensive docs: TRIGGER_MONITOR.md + QUICK_START_TRIGGERS.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>" || echo "⚠️ Nothing to commit or already committed"

git push || echo "⚠️ Nothing to push or already pushed"

# Pull changes on VM
echo "📥 Pulling changes on VM..."
gcloud compute ssh "${VM_NAME}" --zone="${VM_ZONE}" --command="
    cd ${REMOTE_DIR} && \
    git pull origin main
"

# Make scripts executable on VM
echo "🔧 Setting permissions on VM..."
gcloud compute ssh "${VM_NAME}" --zone="${VM_ZONE}" --command="
    cd ${REMOTE_DIR} && \
    chmod +x scripts/trigger-monitor.py \
             scripts/test-matrix-post.sh \
             scripts/deploy-to-vm.sh
"

# Check Claude binary on VM
echo "🔍 Checking Claude Code installation on VM..."
gcloud compute ssh "${VM_NAME}" --zone="${VM_ZONE}" --command="
    which claude || echo '❌ Claude Code not installed on VM'
"

# Test trigger monitor syntax on VM
echo "✅ Testing trigger monitor syntax on VM..."
gcloud compute ssh "${VM_NAME}" --zone="${VM_ZONE}" --command="
    python3 -m py_compile ${REMOTE_DIR}/scripts/trigger-monitor.py && \
    echo '✅ Syntax check passed'
"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "  1. SSH to VM: gcloud compute ssh ${VM_NAME} --zone=${VM_ZONE}"
echo "  2. Test dry-run: cd ~/src/superalignment-chatroom && python3 scripts/trigger-monitor.py --dry-run --once"
echo "  3. Set up systemd: sudo cp systemd/trigger-monitor.service /etc/systemd/system/"
echo "  4. Start service: sudo systemctl start trigger-monitor"
