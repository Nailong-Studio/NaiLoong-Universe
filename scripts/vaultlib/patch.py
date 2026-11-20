"""Reading, patching and auditing docs/index.html."""

from __future__ import annotations

import pathlib
import re
import urllib.parse
import urllib.request

from .config import INDEX, RELICS, ROOT
from .model import catalogue_bytes

CHIPS_RE = re.compile(r'(<div class="vault-chips">)[\s\S]*?(\r?\n[ \t]*</div>)')
COUNT_RE = re.compile(r'(<p class="vault-count" id="vaultCount" role="status">)([^<]*)(</p>)')
CARDS_RE = re.compile(r'(<div class="vault-grid" id="vaultGrid">)[\s\S]*?(\r?\n[ \t]*</div>)')
ALL_CHIP_RE = re.compile(r'data-cat="all">[^<]*<i>\d+</i>')


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
