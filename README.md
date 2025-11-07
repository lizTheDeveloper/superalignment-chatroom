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

## Conversation Viewers

### Quick Access

| Viewer | Port | URL | Status |
|--------|------|-----|--------|
| **Data-Integrities** | 3101 | http://localhost:3101 | ✅ Running |
| **Linda Viewer** | 3102 | http://localhost:3102 | ✅ Running |
| **LatentScope** | 5004 | http://localhost:5004 | ✅ Running |

**Data:** 2,198 conversations (1.7GB)

### Data-Integrities Viewer (Primary)

Server-side viewer that automatically loads all conversations:

```bash
cd ~/src/superalignment-chatroom/claude-history-viewer
npm start
```

Visit http://localhost:3101 to browse 2,060+ conversations with full-text search and markdown export.

### Linda Viewer (Alternative)

Drag & drop client-side viewer:

```bash
cd /tmp/linda-viewer
PORT=3102 npm run dev
```

Visit http://localhost:3102 and drag JSONL files. **Hosted version:** https://jsonl.withlinda.dev

### LatentScope

Interactive embedding visualization for exploring conversation clusters:

```bash
cd ~/src/superalignment-chatroom
./start_latentscope.sh > logs/latentscope.log 2>&1 &
```

Visit http://localhost:5004 for UMAP projections, clustering, and semantic exploration.

**Features:**
- 🔍 **Semantic search** across conversation embeddings
- 📊 **UMAP projection** - 2D visualization
- 🎯 **HDBSCAN clustering** - Identify conversation groups
- 🚀 **Local embeddings** - QWEN3-Embedding-0.6B (no API keys)

**Status:** ⚠️ **INCOMPLETE - NEEDS RE-RUN** (Nov 5, 2025)
- ✅ 2,198 conversations chunked → 30,472 chunks (173MB)
- ✅ Chunks ingested to LatentScope (75MB parquet)
- ❌ QWEN3 embedding batch incomplete (518/7,618 batches = 6.8%)
- ❌ UMAP/clustering not started (requires embeddings)
- 📝 Test dataset exists (98 files, wrong model - for development only)

**To Complete:**
```bash
cd ~/src/superalignment-chatroom
source latentscope-venv/bin/activate
export LATENT_SCOPE_DATA=~/.latentscope-data
bash scripts/batch_process_all.sh > logs/batch_process_$(date +%Y%m%d_%H%M%S).log 2>&1 &
# Will take ~8-10 hours
```

See [CONVERSATION_VIEWER.md](CONVERSATION_VIEWER.md) for complete documentation.

## Related Projects

- [superalignmenttoutopia](https://github.com/yourusername/superalignmenttoutopia) - Main simulation project
