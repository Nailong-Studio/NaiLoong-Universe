# Versioning & Release Policy

This repository follows [Semantic Versioning 2.0.0](https://semver.org/) with the
site-specific scheme `MAJOR.MINOR.PATCH`, written as `vMAJOR.MINOR.PATCH`.

Every repository in the `Nailong-Studio` organisation ships **exactly one**
machine-readable version per release, and that version must agree everywhere it
appears:

| Location | Purpose |
| --- | --- |
| `VERSION` | single source of truth, read by tooling |
| `CHANGELOG.md` | newest entry must match `VERSION` |
| Git tag `vX.Y.Z` | must point at the commit that released it |
| Service worker cache (`nw-vX.Y.Z`) | must match `VERSION`, otherwise PWA clients keep stale shells |
| GitHub Release | title starts with the same `vX.Y.Z` |

## When to bump which digit

| Digit | Bump when | Examples |
| --- | --- | --- |
| **MAJOR** | A visitor-visible contract breaks: URL scheme, hash routes, public data schema, or a required file is removed | Renaming `#halls`, dropping a field from `collection.json`, deleting `assets.json` keys |
| **MINOR** | New capability, new content class, new hall, new page — backwards compatible | New gallery wing, new vault category, new PWA feature |
| **PATCH** | Fixes with no new surface: broken links, copy corrections, accessibility fixes, dependency bumps | Repairing the vault hrefs, correcting a count, fixing a typo |

Because this is a content site rather than a library, a MAJOR bump is rare:
adding or removing artwork is MINOR, and repairing metadata is PATCH.

## Release checklist

1. Update `VERSION` and add a `CHANGELOG.md` entry under the new heading.
2. Run the local gates (see below); all of them must pass before tagging.
3. Commit with an imperative subject, e.g. `fix: repair vault original links`.
4. `git tag -a vX.Y.Z -m "..."` and push the tag together with `main`.
5. Create the GitHub Release from that tag; the notes are the CHANGELOG section.
6. Verify the deployed site and every download artifact before announcing.

## Local gates

```bash
python scripts/check_site.py --manifest assets.json
```

`scripts/check_site.py` is the single entry point and runs every gate:

* vault cards match the wallpaper manifest, and no href is double-encoded
* `docs/data/collection.json` matches the halls and works in `docs/index.html`
* every referenced thumbnail exists on disk
* the inline script parses, and tag/brace balance is intact
* `VERSION`, the newest CHANGELOG heading and the service-worker cache agree

CI runs exactly the same command (`.github/workflows/content-check.yml`), so a
green local run and a green pull request mean the same thing. Never bypass a red
gate by editing the check — fix the content instead.

## Historical note

Versions before `v18.0.0` used an ad-hoc `v17.x` scheme where MINOR numbers did
not map to features and PATCH numbers drifted from the Service Worker cache.
`v18.0.0` resets the line to strict SemVer; the old tags stay in history and are
not renumbered.
