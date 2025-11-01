# Citation Checking in Chatroom Repository

This repository now includes citation verification infrastructure to ensure research integrity in agent conversations.

## Components

### 1. `/check_citation` Slash Command

**Location:** `.claude/commands/check_citation.md`

**Usage:** Type `/check_citation` in Claude Code to verify citations in the previous message.

**What it does:**
- Extracts all citations from the previous message
- Checks against verified citation database
- Downloads and verifies papers when available
- Checks that claims match actual paper content
- Reports findings with evidence quotes

**Example:**
```
User: According to Patterson et al. (2022), GPT-3 used 1,287 MWh of energy.
User: /check_citation
```

The agent will verify:
1. Does Patterson et al. (2022) exist?
2. Is the title/journal correct?
3. Does the paper actually claim 1,287 MWh?
4. Quote the specific passage that supports this

### 2. Post-Commit Hook

**Location:** `.git/hooks/post-commit`

**What it does:**
- Automatically runs after each commit
- Checks if conversation files were modified
- Runs citation verification on changed conversations
- Uses the main repo's citation checker script
- Non-blocking: warns but doesn't fail the commit

**Behavior:**
- ✅ All citations verified → Silent success
- ⚠️ Unverified citations found → Warning with suggestion to run `/check_citation`

### 3. Citation Checker Script

**Location:** `/Users/annhoward/src/superalignmenttoutopia/scripts/citationChecker.py`

The post-commit hook references the citation checker from the main repo. This script:
- Extracts citations using regex patterns
- Checks against multiple verified databases:
  - `research/CITATION_CORRECTIONS_APPLIED_*.md`
  - `docs/wiki/BIBLIOGRAPHY.md`
  - `research/pdf_review_*.md`
  - `.claude/chatroom/research-consensus-*.txt`
  - `research/suspicious_citations_20251029.json`

**Database Status Levels:**
- ✅ VERIFIED - In verified database
- ⚠️ VERIFIED BUT FLAGGED - Verified but suspicious
- ❌ SUSPICIOUS - In suspicious list
- ❓ UNVERIFIED - Not found (possible hallucination)

## How It Works

### Automatic Verification (Post-Commit)

```bash
# You commit a conversation file
git add conversations/research_discussion_20251101.txt
git commit -m "Research discussion on climate tipping points"

# Hook automatically runs
🔍 Running citation verification on conversation messages...
Running citation verification...
⚠️  Warning: Some citations may need verification
    Run /check_citation command to verify specific claims
```

### Manual Verification (Slash Command)

```
Agent: According to Lenton et al. (2023), climate tipping points...

You: /check_citation

Agent:
🔍 CITATION VERIFICATION REPORT

Total citations: 1
✅ Verified: 1
❌ Unverified: 0

DETAILED FINDINGS:

1. Lenton et al. (2023)
   Database: ✅ VERIFIED
   Claim: "climate tipping points cascade at 1.5°C"
   Paper verification: ✅ CONFIRMED
   Evidence: "...tipping cascades initiated around 1.5°C..." (p. 12)
```

## Two-Layer Verification

The citation checking system performs **two layers** of verification:

### Layer 1: Citation Existence
- Does the paper actually exist?
- Are author names, years, titles accurate?
- Is the paper accessible (not a phantom publication)?

### Layer 2: Claim Verification (CRITICAL)
- Does the paper ACTUALLY support the claim made?
- Quote the specific passage from the paper
- Detect misinterpretations, extrapolations, cherry-picking

**Common Issues Caught:**
- Paper discusses topic but doesn't provide the specific value cited
- Value extrapolated beyond paper's scope
- Misinterpretation of findings
- Cherry-picking without context

## Integration with Main Repo

The chatroom repo uses the citation infrastructure from the main repo:

```
superalignmenttoutopia/           # Main repo
├── scripts/
│   ├── citationChecker.py        ← Referenced by chatroom hook
│   ├── autoSearchCitations.py
│   └── verifyCitationWithAutoResearch.py
├── research/
│   └── CITATION_CORRECTIONS_*.md  ← Verified database
└── docs/wiki/BIBLIOGRAPHY.md      ← Verified database

superalignment-chatroom/          # Chatroom repo
├── .claude/commands/
│   └── check_citation.md         ← Slash command
└── .git/hooks/
    └── post-commit               ← Auto-verification
```

## Best Practices

1. **Use `/check_citation` after research discussions**
   - Especially when agents cite papers they haven't seen
   - Before accepting research claims at face value

2. **Pay attention to post-commit warnings**
   - Warning doesn't block commit (non-critical)
   - But indicates citations need manual review

3. **Trust but verify**
   - Even "verified" citations can have incorrect claims
   - Layer 2 (claim verification) is critical

4. **Add new verified citations to database**
   - When you verify a citation manually
   - Add to `research/CITATION_CORRECTIONS_APPLIED_*.md` in main repo
   - Prevents future false positives

## Testing

Test the post-commit hook:

```bash
cd ~/src/superalignment-chatroom

# Create a test conversation with a citation
echo "According to Patterson et al. (2022), GPT-3 used 1,287 MWh." > conversations/test.txt

git add conversations/test.txt
git commit -m "Test citation verification"

# Should output:
# 🔍 Running citation verification on conversation messages...
# Running citation verification...
# ✅ All citations verified (or ⚠️ warning if unverified)
```

Test the slash command in Claude Code:

```
User: According to Smith et al. (2024), transformers improved 10x.
User: /check_citation
```

## Troubleshooting

**"Citation checker not found"**
→ Verify main repo path: `/Users/annhoward/src/superalignmenttoutopia/scripts/citationChecker.py`

**"No citations detected"**
→ Check citation format: Must be "Author et al. (YYYY)" or "Author (YYYY)"

**"HTTP 429 error"**
→ Rate limited. Wait 1 minute and retry.

**Hook doesn't run**
→ Verify hook is executable: `chmod +x .git/hooks/post-commit`

## Related Documentation

- Main repo: `docs/CITATION_VERIFICATION_SYSTEM.md` - Complete system docs
- Main repo: `scripts/CITATION_SCRIPTS_README.md` - Script reference
- Main repo: `docs/CITATION_VERIFICATION_PROTOCOL.md` - Verification protocol

---

**Last updated:** 2025-11-01
**Status:** ✅ Active
