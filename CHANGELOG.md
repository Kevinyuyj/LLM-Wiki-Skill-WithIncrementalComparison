# CHANGELOG

All notable changes to this skill will be documented in this file.

## [1.0.0] — 2026-04-13

### Added

- **Incremental ingest workflow** with SHA256 content hash comparison
- **Manifest-based state tracking** (`.ingest_manifest.json`)
- **Copilot conversation archival** with "painful to re-derive" threshold
- **Complete ingest pipeline**: scan → hash compare → process → update wiki → report
- **Edge case handling**: file deletion, path changes, identical-content moves
- **Full documentation**: README, LICENSE, CHANGELOG, CONTRIBUTING

### Features

- Processes only new or modified files — skips unchanged ones
- Updates `entities/`, `concepts/`, `comparisons/`, `queries/` based on LLM-WIKI schema
- Auto-updates `index.md` and `log.md` after every ingest
- Manifest tracks: `content_hash`, `mtime`, `size`, `processed_at`

### Skill Structure

```
knowledge-ingest/
├── SKILL.md       — Main skill definition (Hermes Agent format)
├── README.md      — Overview and usage
├── LICENSE        — MIT License
├── CHANGELOG.md   — Version history
└── CONTRIBUTING.md — Guidelines
```

## [Unreleased]

- Support for PDF and PPTX ingest via MarkItDown integration
- Git-based change detection as alternative to hash
- Batch processing for large `raw/` directories
