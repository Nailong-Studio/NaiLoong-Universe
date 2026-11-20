"""Vault toolchain package: manifest loading, rendering, patching, auditing."""

from .config import CATEGORY_ORDER, DEFAULT_MANIFEST, INDEX, PARTS_DIR, PARTS_FILE, RELICS, ROOT
from .model import (
    catalogue_bytes,
    items_by_category,
    load_collection,
    load_manifest,
    ordered_categories,
)
from .patch import (
    apply_to_index,
    audit,
    fetch_thumbnails,
    missing_thumbnails,
    read_index,
    update_facts,
    write_index,
)
from .render import human_size, render_card, render_chip, render_vault

__all__ = [
    "CATEGORY_ORDER",
    "DEFAULT_MANIFEST",
    "INDEX",
    "PARTS_DIR",
    "PARTS_FILE",
    "RELICS",
    "ROOT",
    "apply_to_index",
    "audit",
    "catalogue_bytes",
    "fetch_thumbnails",
    "human_size",
    "items_by_category",
    "load_collection",
    "load_manifest",
    "missing_thumbnails",
    "ordered_categories",
    "read_index",
    "render_card",
    "render_chip",
    "render_vault",
    "update_facts",
    "write_index",
]
