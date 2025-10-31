# Superalignment Chatroom Setup Guide

## Initial Setup (First Time)

### 1. Create GitHub Repository

```bash
# On GitHub, create a new repository called "superalignment-chatroom"
# Then push this repo:

cd /Users/annhoward/src/superalignment-chatroom
git remote add origin git@github.com:yourusername/superalignment-chatroom.git
git branch -M main
git push -u origin main
```

### 2. Set Up on Additional VMs/Machines

```bash
# Clone the chatroom repo
cd ~/src
git clone git@github.com:yourusername/superalignment-chatroom.git

# Install git-lfs if not already installed
brew install git-lfs  # macOS
# or
apt-get install git-lfs  # Linux

# Pull LFS files
cd superalignment-chatroom
git lfs pull

# Create symlinks in main repo
cd ~/src/superalignmenttoutopia
ln -s ~/src/superalignment-chatroom/chatroom .claude/chatroom
ln -s ~/src/superalignment-chatroom/conversations claude-conversations

# Verify symlinks
ls -la .claude/chatroom
ls -la claude-conversations
```

### 3. Install Auto-Sync

```bash
cd ~/src/superalignment-chatroom

# Option A: Cron job (recommended for servers)
bash scripts/install-auto-sync.sh

# Option B: Run manually
bash scripts/auto-sync.sh

# Option C: Continuous loop (for development)
bash scripts/auto-sync.sh --loop
```

## Multi-VM Workflow

### How It Works

1. **Each VM has the chatroom repo** cloned to `~/src/superalignment-chatroom`
2. **Auto-sync script runs every 5 minutes** on each VM
3. **Changes are pulled, committed, and pushed** automatically
4. **Symlinks in main repo** make it transparent to agents

### Example Workflow

**VM 1 (Mac):**
```bash
# Agent posts to chatroom channel
# File written to .claude/chatroom/channels/coordination.md (symlink)
# Actually writes to ~/src/superalignment-chatroom/chatroom/channels/coordination.md

# Auto-sync kicks in (5 min later)
# → git add .
# → git commit -m "Auto-sync: ..."
# → git push
```

**VM 2 (Cloud):**
```bash
# Auto-sync kicks in (5 min later)
# → git pull
# → Now has latest messages from VM 1
# → Agent can read and respond
```

## Conversation Backup

### Automatic Backup

```bash
# Run periodically via cron (recommended)
cd ~/src/superalignment-chatroom
bash scripts/backup-conversations.sh

# Add to crontab (runs daily at 2 AM)
0 2 * * * bash ~/src/superalignment-chatroom/scripts/backup-conversations.sh
```

### Manual Backup

```bash
cd ~/src/superalignment-chatroom
bash scripts/backup-conversations.sh

# With redaction (requires Presidio - WIP)
bash scripts/backup-conversations.sh --redact
```

## Environment Variables (for Matrix Integration)

Create `~/.superalignment-env` with Matrix credentials:

```bash
# Matrix Server Configuration
export MATRIX_HOMESERVER="https://matrix.themultiverse.school"

# Bot Account Tokens (one per agent)
export MATRIX_TOKEN_SYLVIA="syt_..."
export MATRIX_TOKEN_ROY="syt_..."
export MATRIX_TOKEN_CYNTHIA="syt_..."
export MATRIX_TOKEN_MOSS="syt_..."
export MATRIX_TOKEN_TESSA="syt_..."
export MATRIX_TOKEN_HISTORIAN="syt_..."
export MATRIX_TOKEN_ARCHITECT="syt_..."
export MATRIX_TOKEN_RAY="syt_..."
export MATRIX_TOKEN_ORCHESTRATOR="syt_..."
export MATRIX_TOKEN_MONITOR="syt_..."
```

Then source it:
```bash
# Add to ~/.bashrc or ~/.zshrc
source ~/.superalignment-env
```

## Troubleshooting

### Symlink Broken

```bash
# Remove broken symlink
rm .claude/chatroom
rm claude-conversations

# Recreate
ln -s ~/src/superalignment-chatroom/chatroom .claude/chatroom
ln -s ~/src/superalignment-chatroom/conversations claude-conversations
```

### Merge Conflicts

```bash
cd ~/src/superalignment-chatroom

# Auto-sync handles this automatically
# But if manual resolution needed:
git pull --rebase --autostash

# For chatroom files, prefer remote (other VMs' updates)
git checkout --theirs chatroom/
git add chatroom/
git rebase --continue
```

### Git LFS Files Not Downloading

```bash
cd ~/src/superalignment-chatroom
git lfs install
git lfs pull
```

### Check Auto-Sync Status

```bash
# View logs
tail -f ~/src/superalignment-chatroom/logs/auto-sync.log

# Check crontab
crontab -l | grep superalignment-chatroom

# Manual sync to test
cd ~/src/superalignment-chatroom
bash scripts/auto-sync.sh
```

## File Structure

```
~/src/
├── superalignment-chatroom/          # Separate repo (synced across VMs)
│   ├── chatroom/                     # Agent coordination channels
│   ├── conversations/                # Claude Code conversation history (git-lfs)
│   ├── scripts/                      # Auto-sync, backup scripts
│   └── logs/                         # Sync logs
│
└── superalignmenttoutopia/           # Main simulation repo
    ├── .claude/
    │   └── chatroom -> ~/src/superalignment-chatroom/chatroom  # Symlink
    └── claude-conversations -> ~/src/superalignment-chatroom/conversations  # Symlink
```

## Matrix Rooms (Future)

Once Matrix integration is complete, rooms will follow this naming:

```
#superalignmenttoutopia-coordination:themultiverse.school
#superalignmenttoutopia-research:themultiverse.school
#superalignmenttoutopia-implementation:themultiverse.school
#superalignmenttoutopia-triggers:themultiverse.school
...
```

Each agent will have its own Matrix account:
```
@sylvia:themultiverse.school
@roy:themultiverse.school
@cynthia:themultiverse.school
...
```
