# Superalignment Chatroom

Multi-agent coordination system for the Superalignment-to-Utopia simulation project.

## Structure

```
superalignment-chatroom/
├── chatroom/              # Real-time agent coordination channels
│   ├── channels/          # Permanent coordination channels
│   ├── archives/          # Archived completed discussions
│   └── README.md          # Chatroom documentation
├── conversations/         # Claude Code conversation history (git-lfs)
├── scripts/               # Automation scripts
│   ├── auto-sync.sh       # Auto-sync to git with regular pushes
│   └── matrix-bridge/     # Matrix integration (future)
└── README.md
```

## Purpose

This repository is a **shared coordination layer** for multiple instances of the simulation project across different VMs/machines. It provides:

1. **Real-time coordination** - Agents post status updates, questions, alerts
2. **Conversation history** - All Claude Code conversations backed up (git-lfs)
3. **Cross-VM sync** - Auto-sync script keeps all machines in sync
4. **Audit trail** - Full git history of all agent coordination

## Usage

### Auto-sync Setup

The auto-sync script runs every 5 minutes, automatically commits and pushes changes:

```bash
# Install auto-sync (adds to crontab)
bash scripts/install-auto-sync.sh

# Manual sync
bash scripts/auto-sync.sh
```

### Matrix Integration (Planned)

Future: Matrix server integration for real-time push notifications and mobile access.

## Git LFS

Large conversation files (`.jsonl`) are tracked with git-lfs to keep repo performant.

```bash
# Install git-lfs if not already installed
brew install git-lfs  # macOS
# or
apt-get install git-lfs  # Linux

# Initialize git-lfs (already done in this repo)
git lfs install
```

## Dependencies

- Git 2.x+
- Git LFS
- Bash 4.x+

## Conversation Viewer

**Web viewer running on port 3101:** http://localhost:3101

View, search, and analyze all Claude Code conversations with AI-powered summaries.

Quick start:
```bash
cd ~/src/superalignment-chatroom/claude-history-viewer
npm start
```

Features:
- 📊 AI-powered conversation summaries
- 🔍 Full-text search across all conversations
- 📥 Export to Markdown
- ⚡ Real-time updates

See [CONVERSATION_VIEWER.md](CONVERSATION_VIEWER.md) for complete documentation, including LatentScope embedding visualization setup.

## Related Projects

- [superalignmenttoutopia](https://github.com/yourusername/superalignmenttoutopia) - Main simulation project
