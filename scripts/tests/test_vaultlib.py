"""Tests for the vault toolchain (stdlib unittest, no third-party deps)."""

from __future__ import annotations

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import build  # noqa: E402
from vaultlib import DEFAULT_MANIFEST, human_size, read_index, render_card, render_vault  # noqa: E402


class BuildTests(unittest.TestCase):
    def test_docs_index_is_built_from_fragments(self):
        text, total = build.build(str(DEFAULT_MANIFEST))
        self.assertEqual(total, 408)
        self.assertEqual(text, read_index(), "docs/index.html is stale: run scripts/build.py")

    def test_assembled_page_has_no_unrendered_placeholder(self):
        text = build.assemble()
        self.assertIn("vault:cards:generated", text)
        self.assertNotIn("vault:cards:generated", build.build(str(DEFAULT_MANIFEST))[0])
        self.assertEqual(text.count("</main>"), 1)


class RenderTests(unittest.TestCase):
    def test_human_size(self):
        self.assertEqual(human_size(0), "0 B")
        self.assertEqual(human_size(194 * 1024), "194 KB")
        self.assertEqual(human_size(3 * 1024 * 1024 + 400 * 1024), "3.4 MB")

    def test_render_card_does_not_double_encode(self):
        item = {
            "category": "classic",
            "title": "充能",
            "narrative": "第一幕",
            "file": "classic/充能.png",
            "raw": "https://example.com/%E5%85%85%E5%BA%85.png",
            "thumb": "thumbs/classic/充能.webp",
            "bytes": 1024,
        }
        card = render_card(item, "圣典")
        self.assertIn("%E5%85%85", card)
        self.assertNotIn("%25E5", card)

    def test_manifest_total_matches_rendered_cards(self):
        from vaultlib import load_manifest

        manifest = load_manifest(DEFAULT_MANIFEST)
        _, cards, total = render_vault(manifest)
        self.assertEqual(total, manifest["total"])
        self.assertEqual(cards.count('class="vault-card"'), total)


if __name__ == "__main__":
    unittest.main()
