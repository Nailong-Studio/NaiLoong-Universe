"""CLI entry point for build_vault.py (kept for backwards compatibility)."""

from __future__ import annotations

import argparse
import re

from .config import DEFAULT_MANIFEST
from .model import load_collection, load_manifest
from .patch import (
    apply_to_index,
    audit,
    fetch_thumbnails,
    read_index,
    update_facts,
    write_index,
)
from .render import render_vault


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Regenerate the vault section of docs/index.html")
    ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST),
                    help="path or URL to the wallpaper assets.json (default: vendored docs/data/assets.json)")
    ap.add_argument("--check", action="store_true", help="verify only, do not write")
    ap.add_argument("--fetch-thumbs", action="store_true",
                    help="download thumbnails missing from docs/assets/relics")
    ap.add_argument("--repo-raw", default="https://nailoong-wallpaper.pages.dev,https://raw.githubusercontent.com/Nailong-Studio/NaiWa-Wallpaper/main",
                    help="comma-separated mirror bases used when --fetch-thumbs is set")
    args = ap.parse_args(argv)

    manifest = load_manifest(args.manifest)
    if args.fetch_thumbs and not args.check:
        fetched = fetch_thumbnails(manifest, [b for b in args.repo_raw.split(",") if b.strip()])
        if fetched:
            print(f"thumbnails fetched: {fetched}")

    original = read_index()
    chips, cards, total = render_vault(manifest)
    updated = apply_to_index(original, chips, cards, total)
    updated = update_facts(updated, manifest, load_collection())

    problems = audit(updated, manifest, total)

    if args.check:
        if updated != original:
            problems.append("docs/index.html is stale: run scripts/build_vault.py")
        for p in problems:
            print(f"FAIL {p}")
        if problems:
            return 1
        print(f"OK vault in sync: {total} items, {len(re.findall(r'data-cat=\"', updated))} chips")
        return 0

    if problems:
        for p in problems:
            print(f"FAIL {p}")
        return 1

    if updated == original:
        print(f"unchanged: {total} items already in sync")
        return 0

    write_index(updated)
    print(f"vault rebuilt: {total} items written to docs/index.html")
    return 0
