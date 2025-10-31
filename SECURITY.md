# Security

This repository contains sensitive information (conversation logs, Matrix credentials) and implements multiple layers of protection against accidental credential exposure.

## Protection Layers

### 1. Pre-commit Hook (Secrets Detection)

**Location:** `.git/hooks/pre-commit`

Automatically scans staged files for secrets before commit. Blocks commits containing:

- **Matrix tokens** (syt_* format)
- **API keys** (Google, OpenAI, Anthropic, AWS, GitHub)
- **Private keys** (RSA, EC, OpenSSH)
- **Service account credentials** (GCP JSON keys)
- **OAuth tokens** (Bearer tokens, refresh tokens)
- **Database connection strings** (mysql://, postgresql://, mongodb://)
- **Billing account numbers**
- **Environment variable exports** with actual secret values

**Testing the hook:**
```bash
# This SHOULD be blocked:
echo "syt_very_secret_token_12345" > test.txt
git add test.txt
git commit -m "test"  # ❌ Hook will block this

# This IS allowed (reference, not actual value):
echo "MATRIX_TOKEN=\${MATRIX_TOKEN_ORCHESTRATOR}" > test.txt
git add test.txt
git commit -m "test"  # ✅ Hook allows this
```

### 2. .gitignore Protection

**Location:** `.gitignore`

Prevents git from tracking sensitive directories/files:

```
# Credentials
matrix-credentials/
*.token
.env
.env.local

# Logs (archived to GCS)
logs/

# Redacted conversations
conversations/sanitized/
conversations/raw/
```

### 3. Conversation Redaction

**Script:** `scripts/redact-conversations.py`

Uses Microsoft Presidio to detect and redact PII from conversation logs:

**Installation:**
```bash
# Install redaction dependencies (optional, script falls back to regex-only mode)
bash scripts/install-redaction-deps.sh
```

**Usage:**
```bash
# Backup with redaction
bash scripts/backup-conversations.sh --redact

# Or run redaction separately
python3 scripts/redact-conversations.py [--emails] [--ips]
```

**Redaction patterns:**
- API keys (Google, OpenAI, Anthropic, AWS, GitHub)
- Private keys and certificates
- GCP service account keys
- Billing account numbers
- Credit cards, SSNs, phone numbers (Presidio)
- **Optional:** Email addresses (`--emails` flag)
- **Optional:** IP addresses (`--ips` flag)

**Output:**
- **Sanitized:** `conversations/sanitized/` (redacted, safe to share)
- **Raw:** `conversations/raw/` (original backups, gitignored)

## Best Practices

### Credentials Management

1. **NEVER commit credentials** - Use environment variables
2. **Store in matrix-credentials/.env** - This directory is gitignored
3. **Export to ~/.superalignment-env** - Source this in shell sessions
4. **Use variable references** - `${MATRIX_TOKEN_ORCHESTRATOR}` not actual tokens

**Example (safe):**
```bash
# In scripts/setup-matrix-bots.sh
echo "MATRIX_TOKEN_ORCHESTRATOR=\"${TOKEN}\"" >> matrix-credentials/.env

# In scripts/install-matrix-mcp.sh (reference, not value)
"env": {
  "MATRIX_ACCESS_TOKEN": "\${MATRIX_TOKEN_ORCHESTRATOR}"
}
```

**Example (unsafe - pre-commit hook will block):**
```bash
# ❌ NEVER do this
echo "MATRIX_TOKEN=syt_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" >> config.sh
git add config.sh  # Hook will block this
```

### Conversation Logs

1. **Redact before sharing** - Use `--redact` flag
2. **Check sanitized output** - Review `conversations/sanitized/` before sharing
3. **Archive raw backups** - Keep originals in `conversations/raw/` (gitignored)
4. **Use git-lfs** - Conversation files are tracked with git-lfs

### GCS Log Archival

Logs are automatically archived to `gs://superalignment-chatroom-logs` daily at 2am:

```bash
# Manual archival
bash scripts/archive-logs-to-gcs.sh

# Manual cleanup
bash scripts/cleanup-logs.sh
```

**Bucket organization:**
```
gs://superalignment-chatroom-logs/
  └── mac.local/2025-01-15_020000/...
  └── claude-workspace/2025-01-15_020000/...
```

## Testing Security

### Test Pre-commit Hook

```bash
# Create test file with fake secret
echo "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" > test-secret.txt
git add test-secret.txt
git commit -m "test"

# Expected output:
# 🔒 Scanning for secrets...
# ❌ SECRETS DETECTED:
#   🔑 Google API key in test-secret.txt
```

### Test Redaction

```bash
# Create test conversation with fake credentials
echo '{"message": {"content": "My API key is sk-ant-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"}}' > conversations/test.jsonl

# Run redaction
python3 scripts/redact-conversations.py

# Check output
cat conversations/sanitized/test.jsonl
# Should show: "My API key is [REDACTED_ANTHROPIC_KEY]"
```

## Emergency: Credential Leak

If credentials are accidentally committed:

1. **Immediately rotate** - Create new tokens/keys
2. **Force push history rewrite** - Use `git filter-branch` or `bfg`
3. **Notify team** - Inform anyone who may have pulled the compromised commit
4. **Review access logs** - Check if credentials were used maliciously

**Prevention is better than cure - the pre-commit hook prevents most accidents.**

## Implementation on Cloud VM

After cloning the repo on the cloud VM:

1. **Hook is already installed** - `.git/hooks/pre-commit` is part of the repo
2. **Credentials via environment** - Set `MATRIX_TOKEN_*` variables
3. **Test the hook** - Try committing a test secret (should be blocked)

The hook runs on both Mac and cloud VM automatically.
