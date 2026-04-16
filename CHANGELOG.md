# CHANGELOG

All notable changes to this skill are documented here.

## [2.3.0] — 2026-04-17

### Added

- **Canvas Export** — `skills/research/llm-wiki/` gains knowledge graph visualization via `knowledge-graph.canvas` (Obsidian native JSON format)
  - Trigger: "generate canvas", "update canvas", "build knowledge graph"
  - Python script at `scripts/generate_canvas.py`
  - Reads wiki path from `~/.hermes/config.yaml` (no hardcoded paths)
  - Scans all wiki pages, resolves wikilinks, outputs `knowledge-graph.canvas`
  - Nodes auto-arranged in grid by page type, then alphabetically
  - Manual trigger only — not part of ingest
- **Manifest CLI (`scripts/manifest.py`)** — Incremental ingest engine codeified as a runnable script
  - `--scan`: report new/changed/deleted files vs manifest
  - `--update`: write current disk state to manifest
  - `--status`: show manifest summary and disk coverage
  - `--diff <filename>`: show hash diff for a specific file
  - Reads wiki path from `~/.hermes/config.yaml` via hermes-agent venv Python
  - Fixed scan paths: includes `raw/` root-level files and `copilot-conversations/`

### Changed

- **Repository restructure** — Combined into monorepo with two skills:
  - `skills/research/llm-wiki/` — Core wiki skill (ingest, query, lint, canvas)
  - `skills/note-taking/knowledge-ingest/` — Incremental ingest enhancement
- **Lint: ⑨ Unexpected connections** — New check added: scan all page pairs, flag pairs where both pages share >=1 tag AND neither has a wikilink to the other. Group by shared tag. Report only, never auto-modify.
- **README** — Rewritten to cover full monorepo: both skills, 12-point lint, canvas export

## [2.2.0] — 2026-04-13

### Changed

- **raw/ accepts .md only** — only `.md` files are processed during ingest; all other formats (PDF, DOCX, PPTX, XLSX, ZIP, MP4, etc.) are silently skipped. Convert source documents to `.md` before ingest if needed.

## [2.1.0] — 2026-04-13

### Added

- **SHA256 content-hash manifest** (`.ingest_manifest.json`) — THE core innovation
  - Each file tracked by its SHA256 hash, not path
  - Persists across sessions for true incremental processing
- **3-way incremental comparison** — new / modified / unchanged / deleted
- **copilot-conversations/ pipeline** — full ingest flow for Q&A archival
  - "Painful to re-derive" threshold: only archive valuable insights
  - Skips: formatting fixes, redundant content, already-covered topics
- **Automated wiki maintenance** — index.md, log.md, manifest all auto-updated after ingest
- **Edge case handling**:
  - File deletion → manifest cleanup
  - Path change → hash detected, no duplicates
  - Same content moved → hash identical, skip

### Documentation

- README with clear "original vs ours" comparison table
- SKILL.md with detailed step-by-step + our modifications highlighted
- Version history showing evolution (1.0 → 2.0 → 2.1)

### Verified Scenarios

| Test | Scenario | Result |
|------|----------|--------|
| 1 | First ingest (empty manifest) | ✅ All files processed, manifest created |
| 2 | Second ingest (no changes) | ✅ All skipped, zero LLM calls |
| 3 | Third ingest (1 new + 1 modified) | ✅ Only 2 processed, 10 skipped |

## [2.0.0] — 2026-04-13

### Changed

- **Major restructure**: Abandoned self-invented `knowledge/notes/diary/` directories
- Aligned with LLM-WIKI original: `entities/`, `concepts/`, `comparisons/`, `queries/`
- Derived notes now go to LLM-WIKI-defined directories only

### Fixed

- `raw/` is sacred — never modified/moved/deleted
- Copilot conversations: read and analyze, never move original files

## [1.0.0] — 2026-04-12

### Added

- Initial knowledge-ingest skill
- Ingest workflow: raw → derived notes
- `knowledge/`, `notes/`, `diary/` directory structure (later abandoned)

---

## Versioning Philosophy

- **2.x.y**: Incremental system additions or improvements
- **x.0.0**: Directory structure or workflow paradigm changes
- **x.y.0**: New features or significant rewrites
