# LLM-WIKI — Incremental Knowledge Base

> Hash-based incremental ingest + knowledge graph visualization + auto-lint for personal wikis built on [Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) pattern.

[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-2.3.0-blue.svg)](skills/research/llm-wiki/SKILL.md)

---

## TL;DR — What Did We Add?

Two major upgrades over the original LLM Wiki:

1. **Incremental Ingest** — Every file is identified by its SHA256 content hash. Only new or changed files are processed — skips everything else.
2. **Canvas Export** — Generate an Obsidian JSON Canvas knowledge graph from the wiki with one command.
3. **Auto-Lint** — 12 health checks keep the wiki consistent: broken links, orphan pages, stale content, contradictions, unexpected connections, and more.

---

## Architecture

```
wiki/
├── .ingest_manifest.json   # Hash manifest — incremental processing state
├── knowledge-graph.canvas   # Obsidian Canvas visualization (generated on demand)
├── raw/                    # Immutable source material
│   ├── articles/           # Web articles, clippings
│   ├── workingdocs/        # Working documents
│   └── diarys/             # Personal notes, diaries
├── entities/               # People, orgs, products, models
├── concepts/               # Topics and concepts
├── comparisons/            # Side-by-side analyses
├── queries/                # Filed Q&A worth preserving
├── SCHEMA.md               # Domain rules & tag taxonomy
├── index.md                # Content catalog
└── log.md                  # Operation log
```

### The Manifest (Incremental Core)

```json
{
  "raw/articles/article.md": {
    "content_hash": "a3f5c8...",
    "mtime": 1744531200,
    "size": 12345,
    "processed_at": "2026-04-13T10:00:00Z"
  }
}
```

---

## Skills

This repository contains two complementary skills:

### `skills/research/llm-wiki/` — Core Wiki Skill

The main LLM Wiki skill. Handles:
- **Ingest** — Integrate sources into the wiki with incremental hash comparison
- **Query** — Answer questions from the compiled knowledge base
- **Lint** — 12 automated health checks (see below)
- **Canvas Export** — Generate `knowledge-graph.canvas` on demand

### `skills/note-taking/knowledge-ingest/` — Ingest Enhancement

Extends the wiki with:
- **Incremental processing** — SHA256 hash compare, skip unchanged files
- **Manifest tracking** — `.ingest_manifest.json` persists state across sessions
- **copilot-conversations/ pipeline** — Archive valuable Q&A to `queries/`

---

## 12-Point Lint Check

Every check is **read-only** — never auto-modifies content.

| # | Check | Severity |
|---|-------|----------|
| ① | Orphan pages — no inbound wikilinks | High |
| ② | Broken wikilinks — target doesn't exist | High |
| ③ | Index completeness — missing from `index.md` | Medium |
| ④ | Frontmatter validation — required fields, valid tags | Medium |
| ⑤ | Stale content — >90 days without update | Low |
| ⑥ | Contradictions — conflicting claims on same topic | High |
| ⑦ | Page size — over 200 lines (candidate for split) | Low |
| ⑧ | Tag audit — tags not in taxonomy | Medium |
| ⑨ | Unexpected connections — shared tags but no reciprocal link | Low |
| ⑩ | Log rotation — rotate if >500 entries | Low |
| ⑪ | Report findings — grouped by severity | — |
| ⑫ | Append to `log.md` | — |

---

## Usage

```bash
# Ingest new sources (incremental — only new/changed files)
ingest

# Query the wiki
ask "what do we know about X?"

# Health check the wiki
lint

# Generate knowledge graph canvas
generate canvas
```

No configuration needed. Just speak what you want.

---

## Quick Start

```bash
# Trigger ingest — everything else is automatic
ingest

# Trigger lint
lint

# Generate canvas
generate canvas
```

---

## Tech Stack

- **SHA256** — Content identity via `shasum -a 256` (no external deps)
- **Hermes Agent** — AI agent framework
- **Obsidian** — Knowledge base frontend + Canvas visualization
- **LLM-WIKI** — Knowledge organization pattern by Andrej Karpathy

---

## Related

- [Karpathy's LLM Wiki (original)](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [Hermes Agent](https://github.com/nousresearch/hermes-agent)
- [Obsidian](https://obsidian.md/)
