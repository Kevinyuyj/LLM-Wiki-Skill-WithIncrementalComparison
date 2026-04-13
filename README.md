# LLM-WIKI Ingest Skill — Incremental Version

> Hash-based incremental ingest for personal knowledge bases. Only processes new and modified files — skips everything else.

[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-2.2.0-blue.svg)](SKILL.md)

---

## TL;DR — What Did We Add?

This skill builds on [Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) with one key improvement:

> **Every file is identified by its SHA256 content hash, not its path or filename.**
> When you run `ingest`, only new or changed files are processed.

---

## Core Problem We Solved

The original LLM-WIKI approach re-reads and re-analyzes **every file** on every ingest — even files that haven't changed. This is wasteful when your knowledge base grows to dozens or hundreds of sources.

**Our solution:** A manifest tracks the SHA256 hash of every file. On each ingest, we compare current hashes against the manifest:

```
manifest:  raw/article.md  → hash "abc123..."
disk now:  raw/article.md  → hash "abc123..."  → SAME, skip
disk now:  raw/new.md      → hash not in manifest → PROCESS
disk now:  raw/old.md      → hash "xyz789..."  → hash changed → PROCESS
```

---

## Architecture

```
wiki/
├── .ingest_manifest.json   # Hash manifest — THE key innovation
├── raw/                    # Immutable source material
│   ├── articles/
│   ├── workingdocs/
│   └── diarys/
├── entities/               # People, orgs, products, models
├── concepts/               # Topics and concepts
├── comparisons/            # Side-by-side analyses
├── queries/                # Filed Q&A worth preserving
├── SCHEMA.md               # Domain rules & tag taxonomy
├── index.md                # Content catalog
└── log.md                 # Operation log
```

### The Manifest

```json
{
  "raw/articles/article.md": {
    "content_hash": "a3f5c8...",   // SHA256 of file content
    "mtime": 1744531200,
    "size": 12345,
    "processed_at": "2026-04-13T10:00:00Z"
  }
}
```

The manifest is the single source of truth for incremental state.

---

## How It Works

### The 3-Way File Check (Step 3 of ingest)

| Disk | Manifest | Action |
|------|----------|--------|
| File exists | Hash differs | **Re-process** — content changed |
| File exists | Not in manifest | **New file** — process |
| File exists | Hash same | **Skip** — nothing to do |
| Not on disk | Exists in manifest | **Remove** from manifest |

### Key Insight: Hash > Path

If you move `raw/article.md` to `raw/diarys/article.md`, the hash is identical — we detect this and skip processing. No duplicate entries, no wasted LLM calls.

---

## Usage

```
You: "ingest"

→ Agent scans raw/ and copilot-conversations/
→ Computes SHA256 for each file
→ Compares against .ingest_manifest.json
→ Processes only new or changed files
→ Updates entities/concepts/queries pages
→ Auto-updates index.md, log.md, manifest
→ Reports results
```

No configuration needed. Just say "ingest".

---

## What We Added (vs Original LLM-WIKI)

> **Note:** `raw/` only accepts `.md` files. All other formats (PDF, DOCX, PPTX, XLSX, ZIP, MP4, etc.) are silently skipped. Convert documents to `.md` first if they need to be ingested.

| Feature | Original | Ours |
|---------|----------|------|
| Incremental processing | ❌ Re-processes everything | ✅ SHA256 hash compare |
| Manifest state | ❌ None | ✅ `.ingest_manifest.json` |
| Path-change handling | ❌ Creates duplicates | ✅ Hash = identity, no duplicates |
| File deletion detection | ❌ None | ✅ Manifest cleanup |
| copilot-conversations/ | ❌ Not defined | ✅ Full pipeline with "painful to re-derive" threshold |
| Wiki auto-maintenance | ❌ Manual | ✅ index + log + manifest all updated |
| .DS_Store filtering | ❌ May be processed | ✅ Explicitly filtered |

---

## copilot Conversation Archival

Not all conversations are worth keeping. We use the same standard as wiki queries:

**Archive to `queries/` when the answer is "painful to re-derive"** — meaning:
- Specific tricks or workarounds discovered through experimentation
- Complex reasoning chains you'd have to rebuild from scratch
- Tool-specific insights not easily found elsewhere

**Skip when:**
- Pure formatting fixes (table alignment, Markdown syntax)
- Content already covered in existing wiki pages
- Simple Q&A that could be answered instantly

---

## Auto-Maintenance

After every ingest, these are updated automatically:

1. **index.md** — New pages added to catalog, total count incremented
2. **log.md** — Every operation recorded with timestamp
3. **manifest** — New/modified entries added, deleted entries removed

---

## Verification — Tested Three Scenarios

| Scenario | Expected | Result |
|----------|----------|--------|
| First ingest (empty manifest) | All files processed, manifest created | ✅ |
| Second ingest (no changes) | All skipped, zero LLM calls | ✅ |
| Third ingest (1 new + 1 modified) | Only 2 files processed, rest skipped | ✅ |

---

## Tech Stack

- **SHA256** — Content identity via `shasum -a 256` (no external deps)
- **Hermes Agent** — AI agent framework
- **Obsidian** — Knowledge base frontend
- **LLM-WIKI** — Knowledge organization pattern by Andrej Karpathy

---

## Quick Start

```bash
# Trigger ingest — everything else is automatic
ingest
```

The skill runs autonomously:
1. Scans raw/ and copilot-conversations/
2. Hash-compares against manifest
3. Processes new/changed files only
4. Updates all wiki metadata
5. Reports summary

---

## Related

- [Karpathy's LLM Wiki (original)](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [Hermes Agent](https://github.com/nousresearch/hermes-agent)
- [Obsidian](https://obsidian.md/)
