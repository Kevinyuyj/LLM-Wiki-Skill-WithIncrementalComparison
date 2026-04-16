#!/usr/bin/env python3
"""
Ingest manifest manager for LLM Wiki.

Tracks SHA256 content hashes of all raw source files and copilot conversations.
On each ingest, compares disk state against manifest to determine:
  - New files  → process
  - Changed     → re-process
  - Unchanged   → skip
  - Deleted     → remove from manifest

Usage:
    python3 manifest.py --scan          # Scan and report changes
    python3 manifest.py --update       # Scan and update manifest
    python3 manifest.py --status       # Show manifest summary
    python3 manifest.py --diff <file>  # Show diff for one file

Reads wiki path from config.yaml (skills.config.wiki.path).
No hardcoded paths.
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

CONFIG_PATH = Path.home() / ".hermes" / "config.yaml"
HERMES_PYTHON = "/Users/kevin/.hermes/hermes-agent/venv/bin/python"

# Subdirectories to scan under wiki/raw/
RAW_SUBDIRS = ["articles", "diarys", "WorkingDocs", "papers", "transcripts"]

# Additional top-level scan targets (in wiki root, not under raw/)
EXTRA_SCAN_PATHS = [
    "raw",          # top-level raw files like "Thread by @karpathy.md"
    "copilot/copilot-conversations",
]


def get_wiki_path() -> Path:
    """Read wiki path from ~/.hermes/config.yaml using hermes-agent's Python."""
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


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(wiki_path: Path) -> dict:
    manifest_path = wiki_path / ".ingest_manifest.json"
    if manifest_path.exists():
        with open(manifest_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_manifest(wiki_path: Path, manifest: dict) -> None:
    manifest_path = wiki_path / ".ingest_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def scan_disk(wiki_path: Path) -> dict[str, dict]:
    """Return {relative_path: {content_hash, mtime, size}} for all tracked files."""
    disk = {}
    for subdir in RAW_SUBDIRS:
        d = wiki_path / "raw" / subdir
        if not d.exists():
            continue
        for fp in d.glob("*.md"):
            rel = str(fp.relative_to(wiki_path))
            disk[rel] = {"content_hash": sha256(fp), "mtime": int(fp.stat().st_mtime), "size": fp.stat().st_size}

    for extra in EXTRA_SCAN_PATHS:
        target = wiki_path / extra
        if target.is_file():
            rel = str(target.relative_to(wiki_path))
            disk[rel] = {"content_hash": sha256(target), "mtime": int(target.stat().st_mtime), "size": target.stat().st_size}
        elif target.is_dir():
            for fp in target.glob("*.md"):
                rel = str(fp.relative_to(wiki_path))
                disk[rel] = {"content_hash": sha256(fp), "mtime": int(fp.stat().st_mtime), "size": fp.stat().st_size}

    return disk


def compare_manifest(wiki_path: Path) -> tuple[list, list, list]:
    """Compare disk vs manifest. Returns (new_or_changed, unchanged, deleted)."""
    manifest = load_manifest(wiki_path)
    disk = scan_disk(wiki_path)

    new_or_changed = []
    unchanged = []
    deleted = []

    for rel, data in disk.items():
        if rel not in manifest:
            new_or_changed.append(rel)
        elif manifest[rel]["content_hash"] != data["content_hash"]:
            new_or_changed.append(rel)
        else:
            unchanged.append(rel)

    for rel in manifest:
        if rel not in disk:
            deleted.append(rel)

    return new_or_changed, unchanged, deleted


def cmd_scan(wiki_path: Path) -> None:
    new_or_changed, unchanged, deleted = compare_manifest(wiki_path)
    print(f"Manifest: {len(load_manifest(wiki_path))} entries | Disk: {len(scan_disk(wiki_path))} files")
    print(f"  Unchanged (skip): {len(unchanged)}")
    print(f"  New or changed:   {len(new_or_changed)}")
    print(f"  Deleted:          {len(deleted)}")
    if new_or_changed:
        print("\nNew / Changed:")
        for rel in sorted(new_or_changed):
            print(f"  + {rel}")
    if deleted:
        print("\nDeleted:")
        for rel in sorted(deleted):
            print(f"  - {rel}")


def cmd_update(wiki_path: Path) -> None:
    manifest = load_manifest(wiki_path)
    disk = scan_disk(wiki_path)
    now = datetime.now(timezone.utc).isoformat()

    for rel, data in disk.items():
        manifest[rel] = {
            "content_hash": data["content_hash"],
            "mtime": data["mtime"],
            "size": data["size"],
            "processed_at": manifest.get(rel, {}).get("processed_at", now)
        }

    # Remove deleted entries
    disk_keys = set(disk.keys())
    to_remove = [rel for rel in manifest if rel not in disk_keys]
    for rel in to_remove:
        del manifest[rel]

    save_manifest(wiki_path, manifest)
    new_or_changed, unchanged, deleted = compare_manifest(wiki_path)
    print(f"Manifest updated: {len(manifest)} entries")
    if new_or_changed:
        print(f"  Marked for reprocessing: {len(new_or_changed)}")
        for rel in sorted(new_or_changed):
            print(f"    + {rel}")
    if deleted:
        print(f"  Removed deleted entries: {len(deleted)}")
    if unchanged:
        print(f"  Unchanged (skip on next ingest): {len(unchanged)}")


def cmd_status(wiki_path: Path) -> None:
    manifest = load_manifest(wiki_path)
    disk = scan_disk(wiki_path)
    print(f"Wiki: {wiki_path}")
    print(f"Manifest entries: {len(manifest)}")
    print(f"Disk files tracked: {len(disk)}")
    missing = set(manifest.keys()) - set(disk.keys())
    if missing:
        print(f"Manifest entries missing from disk: {len(missing)}")
        for rel in sorted(missing):
            print(f"  - {rel}")
    else:
        print("All manifest entries present on disk.")


def cmd_diff(wiki_path: Path, filename: str) -> None:
    manifest = load_manifest(wiki_path)
    disk = scan_disk(wiki_path)
    # Try partial match
    matches = [rel for rel in disk if filename in rel]
    if not matches:
        print(f"No file matching '{filename}' found on disk.")
        return
    for rel in matches:
        in_manifest = rel in manifest
        old_hash = manifest[rel]["content_hash"] if in_manifest else "(none)"
        new_hash = disk[rel]["content_hash"]
        status = "CHANGED" if in_manifest and old_hash != new_hash else ("NEW" if not in_manifest else "UNCHANGED")
        print(f"{status}: {rel}")
        print(f"  Old hash: {old_hash}")
        print(f"  New hash: {new_hash}")


def main() -> None:
    parser = argparse.ArgumentParser(description="LLM Wiki Ingest Manifest Manager")
    parser.add_argument("--scan", action="store_true", help="Scan and report changes")
    parser.add_argument("--update", action="store_true", help="Scan and update manifest")
    parser.add_argument("--status", action="store_true", help="Show manifest summary")
    parser.add_argument("--diff", metavar="FILE", help="Show diff for a specific file")
    args = parser.parse_args()

    wiki_path = get_wiki_path()
    if not wiki_path.exists():
        print(f"ERROR: Wiki path does not exist: {wiki_path}", file=sys.stderr)
        sys.exit(1)

    if args.scan:
        cmd_scan(wiki_path)
    elif args.update:
        cmd_update(wiki_path)
    elif args.status:
        cmd_status(wiki_path)
    elif args.diff:
        cmd_diff(wiki_path, args.diff)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
