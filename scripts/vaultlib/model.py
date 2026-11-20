"""Loading and normalising the wallpaper manifest."""

from __future__ import annotations

import json
import pathlib
import urllib.parse
import urllib.request

from .config import CATEGORY_ORDER, COLLECTION, DEFAULT_MANIFEST


def load_manifest(source: str | pathlib.Path | None = None) -> dict:
    """Read a manifest from a path or URL.

    Passing ``None`` uses the vendored ``docs/data/assets.json`` so offline
    builds and CI runs do not depend on the wallpaper CDN being reachable.
    """
    if source is None:
        source = DEFAULT_MANIFEST
    source = str(source)
    if source.startswith(("http://", "https://")):
        req = urllib.request.Request(source, headers={"User-Agent": "naiwa-vault-builder"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    return json.loads(pathlib.Path(source).read_text(encoding="utf-8"))


def load_collection() -> dict | None:
    """Read the exported catalogue, if present (it drives the hero stats)."""
    if not COLLECTION.exists():
        return None
    return json.loads(COLLECTION.read_text(encoding="utf-8"))


def ordered_categories(manifest: dict) -> list[dict]:
    """Categories in editorial order, with unknown ones appended alphabetically."""
    known = {c["id"]: c for c in manifest.get("categories", [])}
    ordered = [known[cid] for cid in CATEGORY_ORDER if cid in known]
    leftover = sorted(
        (c for cid, c in known.items() if cid not in CATEGORY_ORDER),
        key=lambda c: c["id"],
    )
    return ordered + leftover


def items_by_category(manifest: dict) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for item in manifest.get("items", []):
        grouped.setdefault(item["category"], []).append(item)
    return grouped


def catalogue_bytes(collection: dict | None, manifest: dict) -> int:
    """Sum the byte sizes of the originals the catalogue actually links to.

    The catalogue stores percent-encoded raw URLs; map them back to manifest
    entries by repository path so the headline figure describes the museum's
    own holdings rather than the whole wallpaper warehouse.
    """
    if not collection:
        return 0
    by_path = {item["file"]: int(item.get("bytes") or 0) for item in manifest.get("items", [])}
    total = 0
    for item in collection.get("items", []):
        original = item.get("original") or ""
        if "/main/" not in original:
            continue
        path = urllib.parse.unquote(original.split("/main/", 1)[1])
        total += by_path.get(path, 0)
    return total
