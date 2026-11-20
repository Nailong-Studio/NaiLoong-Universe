#!/usr/bin/env python3
"""Build docs/index.html from src/parts/*.html plus the generated vault block.

Source of truth is ``src/``: page fragments in ``src/parts/`` are concatenated
in ``src/parts.json`` order, then the vault chips/cards and the hero statistics
are derived from ``docs/data/assets.json`` and ``docs/data/collection.json``.
``docs/index.html`` stays a single self-contained file because that is what the
museum ships; it is a build artifact and should not be hand-edited.

Usage:
    python scripts/build.py            # rebuild docs/index.html
    python scripts/build.py --check    # fail if docs/index.html is stale
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from vaultlib import (  # noqa: E402
    DEFAULT_MANIFEST,
    INDEX,
    PARTS_DIR,
    PARTS_FILE,
    ROOT,
    apply_to_index,
    audit,
    load_collection,
    load_manifest,
    read_index,
    render_vault,
    update_facts,
)

REQUIRED_HEAD = "<!DOCTYPE html>"
REQUIRED_TAIL = "</html>"
PLACEHOLDER = "vault:cards:generated"


def assemble() -> str:
    """Join the page fragments and normalize line endings to LF."""
    names = json.loads(PARTS_FILE.read_text(encoding="utf-8"))
    if not names:
        raise SystemExit("error: src/parts.json is empty")
    chunks: list[str] = []
    for name in names:
        path = PARTS_DIR / name
        if not path.exists():
            raise SystemExit(f"error: missing fragment {path.relative_to(ROOT)}")
        with path.open(encoding="utf-8", newline="") as fh:
            chunks.append(fh.read())
    text = "".join(chunks)
    if not text.startswith(REQUIRED_HEAD):
        raise SystemExit("error: assembled page does not start with <!DOCTYPE html>")
    if not text.rstrip().endswith(REQUIRED_TAIL):
        raise SystemExit("error: assembled page does not end with </html>")
    if PLACEHOLDER not in text:
        raise SystemExit("error: vault placeholder missing from src/parts")
    if text.count("</main>") != 1:
        raise SystemExit("error: expected exactly one </main> in fragments")
    return text


def build(manifest_path: str) -> tuple[str, int]:
    manifest = load_manifest(manifest_path)
    text = assemble()
    chips, cards, total = render_vault(manifest)
    text = apply_to_index(text, chips, cards, total)
    text = update_facts(text, manifest, load_collection())
    problems = audit(text, manifest, total)
    if problems:
        for problem in problems:
            print(f"FAIL {problem}")
        raise SystemExit(1)
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return text, total


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build docs/index.html from src/ fragments")
    ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST),
                    help="path or URL to assets.json (default: vendored docs/data/assets.json)")
    ap.add_argument("--check", action="store_true", help="verify docs/index.html is up to date")
    args = ap.parse_args(argv)

    text, total = build(args.manifest)

    if args.check:
        current = read_index()
        if current != text:
            print("FAIL docs/index.html is stale: run python3 scripts/build.py")
            return 1
        print(f"OK docs/index.html in sync: {total} cards, {len(text):,} chars")
        return 0

    current = read_index()
    if current == text:
        print(f"unchanged: {total} cards already in sync")
        return 0

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False,
                                     dir=str(INDEX.parent)) as tmp:
        tmp.write(text)
        tmp_path = pathlib.Path(tmp.name)
    tmp_path.replace(INDEX)
    print(f"built docs/index.html: {total} cards, {len(text):,} chars")
    return 0


if __name__ == "__main__":
    sys.exit(main())
