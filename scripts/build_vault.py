#!/usr/bin/env python3
"""Regenerate the "圣物全图鉴" (vault) block inside docs/index.html from the
wallpaper repository manifest.

The vault section is generated content: chips, cards and counters are derived
from ``assets.json`` published by NaiWa-Wallpaper. Hand-editing them is how a
double-percent-encoding bug (``%25E5``) slipped into 385 links, so this script
owns that region instead.

Usage:
    python scripts/build_vault.py --manifest path/to/assets.json
    python scripts/build_vault.py --manifest https://.../assets.json
    python scripts/build_vault.py --manifest assets.json --check

``--check`` never writes: it fails (exit 1) when the HTML drifts from the
manifest, when a thumbnail is missing, or when a link is double-encoded.
"""

from __future__ import annotations

import argparse
import html
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
INDEX = ROOT / "docs" / "index.html"
RELICS = ROOT / "docs" / "assets" / "relics"

# Category order is editorial, not alphabetical: the vault reads left to right
# from "paintings" to "brand assets", matching the museum narrative.
CATEGORY_ORDER = [
    "classic",
    "laugh-gallery",
    "emotes",
    "poses",
    "poses-wall",
    "pet",
    "art",
    "hd",
    "4k",
    "mobile",
    "frames",
    "videos",
    "fan-videos",
    "audio",
    "assets",
]

MARKER_START = "<!-- vault:generated:start -->"
MARKER_END = "<!-- vault:generated:end -->"

CHIPS_RE = re.compile(r'(<div class="vault-chips">)[\s\S]*?(\r?\n[ \t]*</div>)')
COUNT_RE = re.compile(r'(<p class="vault-count" id="vaultCount" role="status">)([^<]*)(</p>)')
CARDS_RE = re.compile(r'(<div class="vault-grid" id="vaultGrid">)[\s\S]*?(\r?\n[ \t]*</div>)')
ALL_CHIP_RE = re.compile(r'data-cat="all">[^<]*<i>\d+</i>')
SIZE_UNITS = ((1 << 20, "MB", 1), (1 << 10, "KB", 0))


def human_size(num_bytes: int) -> str:
    """Render a byte count the way the cards display it (194 KB / 3.4 MB)."""
    for limit, unit, digits in SIZE_UNITS:
        if num_bytes >= limit:
            return f"{num_bytes / limit:.{digits}f} {unit}"
    return f"{num_bytes} B"


def read_index() -> str:
    """Read docs/index.html verbatim.

    ``newline=""`` keeps the file's CRLF endings intact; without it Python
    translates them to LF and the whole 800 KB file shows up as rewritten.
    """
    with INDEX.open(encoding="utf-8", newline="") as fh:
        return fh.read()


def write_index(text: str) -> None:
    with INDEX.open("w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def load_manifest(source: str) -> dict:
    if source.startswith(("http://", "https://")):
        req = urllib.request.Request(source, headers={"User-Agent": "naiwa-vault-builder"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    return json.loads(pathlib.Path(source).read_text(encoding="utf-8"))


def load_collection() -> dict | None:
    """Read the exported catalogue, if present (it drives the hero stats)."""
    path = ROOT / "docs" / "data" / "collection.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def ordered_categories(manifest: dict) -> list[dict]:
    """Categories in editorial order, with unknown ones appended alphabetically."""
    known = {c["id"]: c for c in manifest.get("categories", [])}
    ordered = [known[cid] for cid in CATEGORY_ORDER if cid in known]
    leftover = sorted((c for cid, c in known.items() if cid not in CATEGORY_ORDER),
                      key=lambda c: c["id"])
    return ordered + leftover


def items_by_category(manifest: dict) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for item in manifest.get("items", []):
        grouped.setdefault(item["category"], []).append(item)
    return grouped


def render_chip(cat: dict, count: int, active: bool) -> str:
    cls = "vault-chip on" if active else "vault-chip"
    return (f'        <button class="{cls}" type="button" data-cat="{cat["id"]}">'
            f'{html.escape(cat["name"])} <i>{count}</i></button>')


def render_card(item: dict, cat_name: str) -> str:
    title = html.escape(item["title"])
    narrative = html.escape(" ".join(item["narrative"].split()))
    cat_label = html.escape(cat_name)
    ext = item["file"].rsplit(".", 1)[-1].upper()
    size = human_size(int(item.get("bytes") or 0))

    # ``raw`` is already percent-encoded by the wallpaper build. Re-quoting it
    # is what produced the %25E5 double encoding — never quote it again.
    href = html.escape(item["raw"], quote=True)
    thumb_name = item["thumb"].split("/")[-1]
    local_thumb = f"assets/relics/{item['category']}/{thumb_name}"

    return (
        f'      <a class="vault-card" data-cat="{item["category"]}" '
        f'data-text="{title} {narrative} {cat_label}" href="{href}" '
        f'target="_blank" rel="noopener" title="{narrative}" '
        f'aria-label="查看《{title}》原图">\n'
        f'        <img loading="lazy" src="{html.escape(local_thumb)}" '
        f'alt="{title}" decoding="async">\n'
        f'        <span class="vault-card__tag">{cat_label}</span>\n'
        f'        <b>{title}</b>\n'
        f'        <small>{ext} · {size}</small>\n'
        f'      </a>'
    )


def render_vault(manifest: dict) -> tuple[str, str, int]:
    """Return (chips_html, cards_html, total)."""
    cats = ordered_categories(manifest)
    grouped = items_by_category(manifest)
    total = sum(len(grouped.get(c["id"], [])) for c in cats)

    chips = [f'        <button class="vault-chip on" type="button" data-cat="all">'
             f'全部 <i>{total}</i></button>']
    for cat in cats:
        count = len(grouped.get(cat["id"], []))
        if count:
            chips.append(render_chip(cat, count, active=False))

    names = {c["id"]: c["name"] for c in cats}
    cards: list[str] = []
    for cat in cats:
        for item in grouped.get(cat["id"], []):
            cards.append(render_card(item, names[item["category"]]))

    return "\n\n".join(chips), "\n".join(cards), total


def missing_thumbnails(manifest: dict) -> list[pathlib.Path]:
    missing = []
    for item in manifest.get("items", []):
        name = item["thumb"].split("/")[-1]
        path = RELICS / item["category"] / name
        if not path.exists():
            missing.append(path)
    return missing


def fetch_thumbnails(manifest: dict, bases: list[str]) -> int:
    """Download vault thumbnails that are not checked in yet.

    Several mirrors are tried in order: raw.githubusercontent is frequently
    reset from mainland networks, the Pages CDN is the primary host anyway.
    """
    fetched = 0
    for item in manifest.get("items", []):
        name = item["thumb"].split("/")[-1]
        dest = RELICS / item["category"] / name
        if dest.exists():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        rel = urllib.parse.quote(item["thumb"])
        last_error: Exception | None = None
        for base in bases:
            url = f"{base.rstrip('/')}/{rel}"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "naiwa-vault-builder"})
                with urllib.request.urlopen(req, timeout=90) as resp:
                    dest.write_bytes(resp.read())
                fetched += 1
                print(f"  fetched {dest.relative_to(ROOT)} from {base}")
                last_error = None
                break
            except Exception as exc:  # noqa: BLE001 - report and try next mirror
                last_error = exc
        if last_error is not None:
            print(f"  FAILED {dest.relative_to(ROOT)}: {last_error}")
    return fetched


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


def update_facts(text: str, manifest: dict, collection: dict | None) -> str:
    """Keep the hero statistic row in sync with the real collections.

    Every number is derived, never typed by hand:
      * 馆藏圣像  — items catalogued in docs/data/collection.json
      * 陈列展厅  — halls declared by that catalogue
      * 圣咏表情  — ``emotes`` items in the wallpaper manifest
      * 典藏原图  — megabytes of the originals behind the catalogue
    """
    works = collection.get("total", 0) if collection else 0
    halls = len(collection.get("halls", [])) if collection else 0
    emotes = sum(1 for i in manifest.get("items", []) if i["category"] == "emotes")
    megabytes = round(catalogue_bytes(collection, manifest) / (1024 * 1024))

    values = [
        (str(works), "馆藏圣像"),
        (str(halls), "陈列展厅"),
        (str(emotes), "圣咏表情"),
        (str(megabytes), "典藏原图"),
    ]
    for number, label in values:
        pattern = re.compile(
            r'(<p class="fact__num">)\d+(<sup>[^<]*</sup></p><p class="fact__label">'
            + re.escape(label) + r"</p>)")
        text, count = pattern.subn(lambda m, num=number: f"{m.group(1)}{num}{m.group(2)}", text, count=1)
        if count != 1:
            raise SystemExit(f"error: statistics row for 「{label}」 not found in docs/index.html")
    return text


def apply_to_index(text: str, chips: str, cards: str, total: int) -> str:
    """Replace the generated regions, matching the file's own line endings.

    docs/index.html is CRLF. Emitting LF here would rewrite the whole 800 KB
    file on every run, so the generated blocks are re-joined with the newline
    style actually present in the document.
    """
    nl = "\r\n" if "\r\n" in text else "\n"
    chips = chips.replace("\n", nl)
    cards = cards.replace("\n", nl)

    chips_block, n_chips = CHIPS_RE.subn(
        lambda m: f"{m.group(1)}{nl}{nl}{chips}{m.group(2)}", text, count=1)
    if n_chips != 1:
        raise SystemExit("error: .vault-chips block not found in docs/index.html")

    cards_block, n_cards = CARDS_RE.subn(
        lambda m: f"{m.group(1)}{nl}{cards}{m.group(2)}", chips_block, count=1)
    if n_cards != 1:
        raise SystemExit("error: #vaultGrid block not found in docs/index.html")

    counted, n_count = COUNT_RE.subn(
        lambda m: f"{m.group(1)}{total} 件{m.group(3)}", cards_block, count=1)
    if n_count != 1:
        raise SystemExit("error: #vaultCount element not found in docs/index.html")
    return counted


def audit(text: str, manifest: dict, total: int) -> list[str]:
    """Structural checks that must hold after generation."""
    problems: list[str] = []
    hrefs = re.findall(r'class="vault-card"[^>]*href="([^"]+)"', text)
    if len(hrefs) != total:
        problems.append(f"card count {len(hrefs)} != manifest total {total}")
    doubled = [u for u in hrefs if "%25" in u]
    if doubled:
        problems.append(f"{len(doubled)} double-encoded href(s), e.g. {doubled[0][:90]}")
    if 'id="vaultCount" role="status">' not in text:
        problems.append("vault counter element missing")
    elif f'role="status">{total} 件' not in text:
        problems.append("vault counter does not match manifest total")
    for path in missing_thumbnails(manifest):
        problems.append(f"missing thumbnail {path.relative_to(ROOT)}")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Regenerate the vault section of docs/index.html")
    ap.add_argument("--manifest", required=True, help="path or URL to the wallpaper assets.json")
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


if __name__ == "__main__":
    sys.exit(main())
