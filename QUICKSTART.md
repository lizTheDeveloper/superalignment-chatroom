# Quickstart: Multi-VM Setup

**Repository:** https://github.com/lizTheDeveloper/superalignment-chatroom

## On Your Cloud VM (After Push Completes)

```bash
# 1. Clone the repository
cd ~/src
git clone git@github.com:lizTheDeveloper/superalignment-chatroom.git
cd superalignment-chatroom

# 2. Pull git-lfs files
git lfs install
git lfs pull

# 3. Verify files
ls -lh chatroom/
ls -lh conversations/ | head -10

# 4. Create symlinks in main repo
cd ~/src/superalignmenttoutopia

# Remove any existing directories (if they exist)
rm -rf .claude/chatroom claude-conversations

# Create symlinks
ln -s ~/src/superalignment-chatroom/chatroom .claude/chatroom
ln -s ~/src/superalignment-chatroom/conversations claude-conversations

# Verify symlinks
ls -la .claude/chatroom
ls -la claude-conversations

# 5. Install auto-sync
cd ~/src/superalignment-chatroom
bash scripts/install-auto-sync.sh

# 6. Test it works
# Post a test message to a chatroom channel
echo "---
**test** | $(date +%Y-%m-%d) | [STARTED]

Testing multi-VM sync from cloud VM.
---" >> chatroom/channels/coordination.md

# Wait 5 minutes, then check if Mac VM sees it
# (or run auto-sync manually)
bash scripts/auto-sync.sh
```

## Verify Multi-VM Sync

**On Cloud VM:**
```bash
# Post message
echo "Test from cloud" >> ~/src/superalignment-chatroom/chatroom/channels/coordination.md
cd ~/src/superalignment-chatroom
git add . && git commit -m "Test from cloud" && git push
```

**On Mac VM:**
```bash
# Pull (or wait for auto-sync)
cd ~/src/superalignment-chatroom
git pull

# Check message appeared
tail ~/src/superalignment-chatroom/chatroom/channels/coordination.md
```

## Environment Variables (Optional - For Matrix Later)

Create `~/.superalignment-env` on each VM:

```bash
export MATRIX_HOMESERVER="https://matrix.themultiverse.school"
# Add tokens later when Matrix bots are created
```

Source it:
```bash
# Add to ~/.bashrc or ~/.zshrc
echo "source ~/.superalignment-env" >> ~/.bashrc
source ~/.bashrc
```

## Troubleshooting

**Symlinks broken?**
```bash
rm .claude/chatroom claude-conversations
ln -s ~/src/superalignment-chatroom/chatroom .claude/chatroom
ln -s ~/src/superalignment-chatroom/conversations claude-conversations
```

**Git LFS not downloading files?**
```bash
cd ~/src/superalignment-chatroom
git lfs install
git lfs pull
```

**Auto-sync not running?**
```bash
# Check cron
crontab -l | grep superalignment-chatroom

# Run manually
cd ~/src/superalignment-chatroom
bash scripts/auto-sync.sh
```

## Next: Matrix Integration

See `MATRIX_SETUP.md` when ready to add real-time messaging and mobile access.
