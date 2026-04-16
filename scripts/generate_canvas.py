#!/usr/bin/env python3
"""
Generate an Obsidian JSON Canvas file from the LLM Wiki.
Reads all wiki pages, extracts [[wikilinks]], and outputs knowledge-graph.canvas.
"""

from __future__ import annotations
import json
import os
import re
import sys
import math
from pathlib import Path
from typing import Optional

WIKI_SUBDIRS = ["entities", "concepts", "comparisons", "queries", "Obsidian"]

HERMES_PYTHON = "/Users/kevin/.hermes/hermes-agent/venv/bin/python"

def get_wiki_path() -> Path:
    """Read wiki path from config.yaml using hermes-agent's Python."""
    import tempfile, subprocess
    script = (
        "import yaml, sys\n"
        "with open('/Users/kevin/.hermes/config.yaml') as f:\n"
        "    c = yaml.safe_load(f)\n"
        "p = c.get('skills',{}).get('config',{}).get('wiki',{}).get('path','')\n"
        "sys.stdout.write(p)"
    )
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(script)
            tmp = f.name
        result = subprocess.run(
            [HERMES_PYTHON, tmp],
            capture_output=True, text=True, timeout=10
        )
        Path(tmp).unlink(missing_ok=True)
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    except Exception:
        pass
    return Path.home() / "wiki"

# Colors for node types
TYPE_COLORS = {
    "entity": "4",      # green
    "concept": "5",      # cyan
    "comparison": "6",   # purple
    "query": "2",        # orange
}


def extract_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from markdown content."""
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}
    fm = {}
    for line in match.group(1).split('\n'):
        if ':' in line:
            key, _, val = line.partition(':')
            fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm


def extract_wikilinks(content: str) -> list[str]:
    """Extract all [[wikilinks]] from markdown content."""
    return re.findall(r'\[\[([^\]]+)\]\]', content)


def slugify(name: str) -> str:
    """Convert a wikilink target to a slug (filename-safe)."""
    return name.lower().replace(' ', '-').replace('_', '-')


def build_wikilink_to_file_map(wiki_path: Path) -> dict[str, Path]:
    """Build a bidirectional map: wikilink text -> file path, with multiple matching strategies."""
    link_to_file: dict[str, Path] = {}
    file_to_wikilink: dict[Path, str] = {}

    for subdir in WIKI_SUBDIRS:
        d = wiki_path / subdir
        if not d.exists():
            continue
        for md in d.glob("*.md"):
            # Primary key: lowercase stem
            link_to_file[md.stem.lower()] = md
            # Also map the frontmatter title if available
            content = md.read_text(encoding="utf-8")
            fm = extract_frontmatter(content)
            title = fm.get("title", "")
            if title:
                link_to_file[title.lower()] = md
                link_to_file[slugify(title)] = md
            # Map from the filename without extension
            link_to_file[md.stem] = md

    return link_to_file


def resolve_wikilink(wikilink: str, link_to_file: dict[str, Path]) -> Optional[Path]:
    """Resolve a [[wikilink]] to a file path using multiple matching strategies."""
    # Strategy 1: exact lowercase stem match
    key = wikilink.lower()
    if key in link_to_file:
        return link_to_file[key]

    # Strategy 2: slugified match
    slug = slugify(wikilink)
    if slug in link_to_file:
        return link_to_file[slug]

    # Strategy 3: partial match — wikilink contains the stem, or stem contains wikilink
    for k, fp in link_to_file.items():
        if wikilink.lower() in k.lower() or k.lower() in wikilink.lower():
            return fp

    return None


def all_wiki_pages(wiki_path: Path) -> list[tuple[Path, dict, str]]:
    """Return list of (filepath, frontmatter, content) for all wiki pages."""
    pages = []
    for subdir in WIKI_SUBDIRS:
        d = wiki_path / subdir
        if not d.exists():
            continue
        for md in d.glob("*.md"):
            content = md.read_text(encoding="utf-8")
            fm = extract_frontmatter(content)
            pages.append((md, fm, content))
    return pages


def extract_page_id(fp: Path, fm: dict) -> str:
    """Generate a stable node ID for a page file."""
    # Prefer frontmatter title if available, otherwise use filename
    title = fm.get("title", fp.stem)
    return slugify(title)


def extract_page_label(fp: Path, fm: dict) -> str:
    """Extract display label from frontmatter title."""
    return fm.get("title", fp.stem)


def extract_page_type(fp: Path, fm: dict) -> str:
    """Determine page type from frontmatter or directory."""
    if fm.get("type"):
        return fm["type"]
    for st in WIKI_SUBDIRS:
        if f"/{st}/" in str(fp):
            return st.rstrip("s")
    return "page"


def grid_position(index: int, total: int = 0, cols: int = 5) -> tuple[int, int]:
    """Simple grid layout: col * col_width, row * row_height."""
    col = index % cols
    row = index // cols
    return col * 420, row * 260

def main():
    wiki_path = get_wiki_path()
    if not wiki_path.exists():
        print(f"ERROR: Wiki path does not exist: {wiki_path}", file=sys.stderr)
        sys.exit(1)

    pages = all_wiki_pages(wiki_path)
    if not pages:
        print("WARNING: No wiki pages found.", file=sys.stderr)
        pages = []

    # Build all page metadata
    # Key by node ID (slugified frontmatter title) so edge creation can find nodes
    page_ids: dict[str, dict] = {}
    for i, (fp, fm, _) in enumerate(pages):
        pid = extract_page_id(fp, fm)
        page_ids[pid] = {
            "id": pid,
            "type": "file",
            "file": str(fp.relative_to(wiki_path)),
            "label": extract_page_label(fp, fm),
            "page_type": extract_page_type(fp, fm),
            "x": 0,
            "y": 0,
            "width": 400,
            "height": 200,
        }

    # Grid layout — sort by page_type then by label for consistent ordering
    type_order = {"entity": 0, "concept": 1, "comparison": 2, "query": 3, "page": 4}
    sorted_pages = sorted(pages, key=lambda p: (type_order.get(p[1].get("type", ""), 5), p[0].stem))
    for i, (fp, fm, _) in enumerate(sorted_pages):
        x, y = grid_position(i)
        pid = extract_page_id(fp, fm)
        if pid in page_ids:
            page_ids[pid]["x"] = x
            page_ids[pid]["y"] = y

    # Build wikilink resolution map once
    link_to_file = build_wikilink_to_file_map(wiki_path)

    # Build edges from wikilinks
    edges_map: dict[str, dict] = {}
    for fp, fm, content in pages:
        from_id = extract_page_id(fp, fm)
        for wl in extract_wikilinks(content):
            target_fp = resolve_wikilink(wl, link_to_file)
            if not target_fp:
                continue
            to_id = extract_page_id(target_fp, extract_frontmatter(target_fp.read_text(encoding="utf-8")))
            if from_id == to_id:
                continue
            edge_id = f"edge-{from_id}-{to_id}"
            if edge_id in edges_map:
                continue
            # Only add edge if both nodes exist in the canvas
            if from_id not in page_ids or to_id not in page_ids:
                continue
            edges_map[edge_id] = {
                "id": edge_id,
                "fromNode": from_id,
                "fromSide": "right",
                "fromEnd": "none",
                "toNode": to_id,
                "toSide": "left",
                "toEnd": "arrow",
            }

    # Assemble canvas JSON
    nodes = list(page_ids.values())
    edges = list(edges_map.values())

    canvas = {"nodes": nodes, "edges": edges}

    output_path = wiki_path / "knowledge-graph.canvas"
    output_path.write_text(json.dumps(canvas, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Generated {output_path}")
    print(f"  Nodes: {len(nodes)}")
    print(f"  Edges: {len(edges)}")


if __name__ == "__main__":
    main()
