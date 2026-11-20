"""Shared paths and constants for the vault toolchain."""

from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
INDEX = ROOT / "docs" / "index.html"
RELICS = ROOT / "docs" / "assets" / "relics"
DEFAULT_MANIFEST = ROOT / "docs" / "data" / "assets.json"
COLLECTION = ROOT / "docs" / "data" / "collection.json"
PARTS_FILE = ROOT / "src" / "parts.json"
PARTS_DIR = ROOT / "src" / "parts"

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
