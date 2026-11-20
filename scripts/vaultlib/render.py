"""Pure renderers for the generated vault block."""

from __future__ import annotations

import html

from .config import RELICS
from .model import items_by_category, ordered_categories

SIZE_UNITS = ((1 << 20, "MB", 1), (1 << 10, "KB", 0))


def human_size(num_bytes: int) -> str:
    """Render a byte count the way the cards display it (194 KB / 3.4 MB)."""
    for limit, unit, digits in SIZE_UNITS:
        if num_bytes >= limit:
            return f"{num_bytes / limit:.{digits}f} {unit}"
    return f"{num_bytes} B"


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
