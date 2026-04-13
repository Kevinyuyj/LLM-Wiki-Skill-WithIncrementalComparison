# LLM-WIKI Ingest Skill — Incremental Version

> Hermes Agent skill for Kevin's personal knowledge base, featuring content-hash-based incremental ingest.

## Overview

This skill implements a **hash-based incremental ingest workflow** for maintaining a personal knowledge wiki built on [Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

Unlike naive approaches that re-process the entire `raw/` directory on every ingest, this skill:

- **Tracks content changes** via SHA256 hash comparison
- **Skips unchanged files** — only processes new or modified content
- **Maintains a manifest** (`.ingest_manifest.json`) for durable state across sessions
- **Handles edge cases**: file deletion, path changes, and same-content moves

## Architecture

```
wiki/
├── .ingest_manifest.json   # Incremental state tracker (content_hash + mtime + size)
├── raw/                    # Layer 1: Immutable source material
│   ├── articles/
│   ├── papers/
│   ├── workingdocs/
│   └── diarys/
├── entities/               # Layer 2: People, organizations, products, models
├── concepts/               # Layer 2: Concepts and topics
├── comparisons/            # Layer 2: Side-by-side analyses
└── queries/                # Layer 2: Filed Q&A worth preserving
```

## Key Features

### Incremental Ingest

| File State | Action |
|------------|--------|
| New file (not in manifest) | Process |
| Content changed (hash differs) | Re-process |
| Content unchanged (hash same) | Skip |
| File deleted from disk | Remove from manifest |

### Copilot Conversation Archival

Conversations from `copilot-conversations/` are analyzed using the same threshold as wiki queries:
- **Worth archiving**: Complex, hard-to-re-derive insights
- **Skip**: Simple Q&A, formatting fixes, redundant content

### Wiki Maintenance

Every ingest automatically:
1. Creates or updates entity/concept/comparison/query pages
2. Updates `index.md` with new entries
3. Appends operation record to `log.md`
4. Refreshes `.ingest_manifest.json`

## Usage

When Kevin says **"ingest"**, this skill activates automatically:

```
Kevin: "ingest"

→ Agent scans raw/ and copilot-conversations/
→ Hash comparison vs manifest
→ Process new/modified files only
→ Update wiki, index, log, manifest
→ Report results
```

## Design Principles

- **Raw is sacred**: Never modify, move, or delete files in `raw/`
- **Content identity via SHA256**: File path changes don't create duplicates
- **No redundant reprocessing**: Hash-based skip saves LLM calls
- **Preserve original conversations**: Copilot files stay untouched, only extracts go to `queries/`

## Schema & Conventions

Each wiki page requires:
- YAML frontmatter (`title`, `created`, `updated`, `type`, `tags`, `sources`)
- At least 2 `[[wikilinks]]` per page
- Tags from the SCHEMA taxonomy only

## Tech Stack

- **Hermes Agent** — AI agent framework
- **Obsidian** — Knowledge base frontend
- **SHA256** — Content identity (fast, no external dependencies)
- **LLM-WIKI** — Knowledge organization pattern

## Related

- [Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [Hermes Agent](https://github.com/nousresearch/hermes-agent)
