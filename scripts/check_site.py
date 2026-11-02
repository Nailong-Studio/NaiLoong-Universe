#!/usr/bin/env python3
"""Single gate for the whole repository: content, links, versions, structure.

Everything CI enforces lives here so that a local run and a pull request give
the same answer. Each check is independent and reports its own failures, so one
broken area never hides another.

Usage:
    python scripts/check_site.py                       # full gate, fetches manifest
    python scripts/check_site.py --manifest assets.json  # use a local manifest
    python scripts/check_site.py --offline             # skip network checks
    python scripts/check_site.py --strict-links        # also probe every href

Exit code is 0 only when every check passes.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
INDEX = DOCS / "index.html"
MANIFEST_URL = "https://nailoong-wallpaper.pages.dev/assets.json"
UA = {"User-Agent": "naiwa-check"}


class Report:
    """Collects failures per section so output stays readable."""

    def __init__(self) -> None:
        self.sections: list[tuple[str, list[str]]] = []

    def section(self, name: str) -> "_Section":
        return _Section(self, name)

    def failed(self) -> bool:
        return any(problems for _, problems in self.sections)

    def render(self) -> None:
        for name, problems in self.sections:
            if problems:
                print(f"FAIL {name}")
                for problem in problems:
                    print(f"  - {problem}")
            else:
                print(f"OK   {name}")


class _Section:
    def __init__(self, report: Report, name: str) -> None:
        self.report = report
        self.name = name
        self.problems: list[str] = []

    def __enter__(self) -> "_Section":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.report.sections.append((self.name, self.problems))

    def fail(self, message: str) -> None:
        self.problems.append(message)

    def expect(self, condition: bool, message: str) -> None:
        if not condition:
            self.fail(message)


def read(path: pathlib.Path) -> str:
    with path.open(encoding="utf-8", newline="") as fh:
        return fh.read()


def load_manifest(source: str | None, offline: bool) -> dict | None:
    if offline:
        return None
    target = source or MANIFEST_URL
    try:
        if target.startswith(("http://", "https://")):
            req = urllib.request.Request(target, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        return json.loads(pathlib.Path(target).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - network is best-effort here
        print(f"warn: manifest unavailable ({exc}); skipping manifest-dependent checks")
        return None


def check_structure(report: Report) -> None:
    with report.section("repository structure") as s:
        for required in ["VERSION", "CHANGELOG.md", "README.md", "LICENSE",
                         "CONTRIBUTING.md", "SECURITY.md", "VERSIONING.md",
                         "docs/index.html", "docs/data/collection.json"]:
            s.expect((ROOT / required).exists(), f"missing required file {required}")
        s.expect(not (ROOT / "site").exists(),
                 "obsolete site/ directory still present (removed in v18.0.0)")


def check_vault(report: Report, manifest: dict | None) -> None:
    with report.section("vault links") as s:
        html = read(INDEX)
        hrefs = re.findall(r'class="vault-card"[^>]*href="([^"]+)"', html)
        s.expect(bool(hrefs), "no vault cards found in docs/index.html")

        doubled = [u for u in hrefs if "%25" in u]
        s.expect(not doubled,
                 f"{len(doubled)} double-encoded vault href(s), e.g. {doubled[0][:100]}" if doubled else "")

        bad_scheme = [u for u in hrefs if not u.startswith("https://")]
        s.expect(not bad_scheme, f"{len(bad_scheme)} vault href(s) are not https")

        if manifest is not None:
            expected = manifest.get("total", len(manifest.get("items", [])))
            s.expect(len(hrefs) == expected,
                     f"vault has {len(hrefs)} cards but the manifest lists {expected} items")
            counter = re.search(r'id="vaultCount" role="status">([^<]*)<', html)
            s.expect(counter is not None and counter.group(1).strip() == f"{expected} 件",
                     f"vault counter is '{counter.group(1).strip() if counter else 'missing'}', expected '{expected} 件'")


def check_thumbnails(report: Report) -> None:
    with report.section("vault thumbnails") as s:
        html = read(INDEX)
        thumbs = set(re.findall(r'class="vault-card".*?<img[^>]*src="(assets/relics/[^"]+)"', html, re.S))
        s.expect(bool(thumbs), "no vault thumbnails referenced")
        missing = [t for t in sorted(thumbs) if not (DOCS / urllib.parse.unquote(t)).exists()]
        for path in missing[:10]:
            s.fail(f"missing thumbnail {path}")
        if len(missing) > 10:
            s.fail(f"... and {len(missing) - 10} more missing thumbnails")


def check_catalogue(report: Report) -> None:
    with report.section("catalogue integrity") as s:
        data = json.loads((DOCS / "data" / "collection.json").read_text(encoding="utf-8"))
        items = data.get("items", [])
        halls = data.get("halls", [])
        s.expect(bool(items), "collection.json has no items")
        s.expect(len(halls) == 8, f"expected 8 halls, found {len(halls)}")
        s.expect(data.get("total") == len(items),
                 f"total {data.get('total')} != item count {len(items)}")

        ids = [i.get("id") for i in items]
        dupes = sorted({x for x in ids if ids.count(x) > 1})
        s.expect(not dupes, f"duplicate catalogue ids: {', '.join(map(str, dupes[:5]))}")

        for hall in halls:
            declared = hall.get("count", 0)
            actual = sum(1 for i in items if i.get("hall") == hall.get("id"))
            s.expect(declared == actual,
                     f"{hall.get('id')} declares {declared} items but has {actual}")

        # An original is either an external URL or a file the site hosts itself.
        broken = []
        for item in items:
            original = i_original = item.get("original") or ""
            if i_original.startswith("https://"):
                continue
            if i_original.startswith("assets/") and (DOCS / i_original).exists():
                continue
            broken.append((item["id"], original))
        s.expect(not broken,
                 f"{len(broken)} item(s) without a usable original, e.g. {broken[:3]}")


def check_versions(report: Report) -> None:
    with report.section("version consistency") as s:
        version = read(ROOT / "VERSION").strip()
        match = re.match(r"v(\d+)\.(\d+)\.(\d+)", version)
        s.expect(match is not None, f"VERSION '{version}' is not vMAJOR.MINOR.PATCH")
        if not match:
            return
        semver = f"v{match.group(1)}.{match.group(2)}.{match.group(3)}"

        changelog = read(ROOT / "CHANGELOG.md")
        headings = re.findall(r"^##\s+v?(\d+\.\d+\.\d+)", changelog, flags=re.M)
        s.expect(bool(headings), "CHANGELOG.md has no versioned headings")
        if headings:
            s.expect(f"v{headings[0]}" == semver,
                     f"CHANGELOG newest entry is v{headings[0]} but VERSION is {semver}")

        sw = read(DOCS / "sw.js")
        cache = re.search(r'VERSION\s*=\s*"nw-v(\d+\.\d+\.\d+)"', sw)
        s.expect(cache is not None, "docs/sw.js has no nw-vX.Y.Z cache version")
        if cache:
            s.expect(f"v{cache.group(1)}" == semver,
                     f"service worker cache is nw-v{cache.group(1)} but VERSION is {semver}")


def check_html(report: Report) -> None:
    with report.section("html integrity") as s:
        html = read(INDEX)
        for tag in ("html", "head", "body"):
            opens = len(re.findall(rf"<{tag}[\s>]", html))
            closes = html.count(f"</{tag}>")
            s.expect(opens == closes, f"<{tag}> unbalanced: {opens} open, {closes} close")
        s.expect(html.count("<section") == html.count("</section>"),
                 f"<section> unbalanced: {html.count('<section')} open, {html.count('</section>')} close")

        scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.S)
        s.expect(bool(scripts), "no inline script found")
        for i, script in enumerate(scripts):
            script = re.sub(r"</script>", "", script, flags=re.I)
            tmp = ROOT / ".tmp-inline.js"
            tmp.write_text(script, encoding="utf-8")
            try:
                result = subprocess.run(["node", "--check", str(tmp)],
                                        capture_output=True, text=True, timeout=120)
                if result.returncode != 0:
                    first = (result.stderr or "").strip().splitlines()
                    s.fail(f"inline script #{i} does not parse: {first[0] if first else 'unknown error'}")
            except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
                s.fail(f"could not syntax-check inline script #{i}: {exc}")
            finally:
                tmp.unlink(missing_ok=True)

        brace_open, brace_close = html.count("{"), html.count("}")
        s.expect(abs(brace_open - brace_close) < 50,
                 f"brace balance drifted: {brace_open} '{{' vs {brace_close} '}}'")


def check_local_links(report: Report) -> None:
    with report.section("local references") as s:
        html = read(INDEX)
        refs = set(re.findall(r'(?:src|href)="((?!https?:|//|#|data:|mailto:)[^"]+)"', html))
        missing = []
        for ref in sorted(refs):
            target = urllib.parse.unquote(ref.split("?")[0].split("#")[0])
            if not target or target.endswith("/"):
                continue
            if not (DOCS / target).exists():
                missing.append(ref)
        for ref in missing[:10]:
            s.fail(f"missing local file referenced by the page: {ref}")
        if len(missing) > 10:
            s.fail(f"... and {len(missing) - 10} more missing local references")


def check_remote_links(report: Report, manifest: dict | None, strict: bool) -> None:
    """Probe a representative sample of outbound links.

    Only a sample: probing 400+ URLs would make CI slow and flaky, and the
    double-encoding bug this gate exists for is systematic, not sporadic.
    """
    with report.section("outbound links") as s:
        html = read(INDEX)
        hrefs = re.findall(r'class="vault-card"[^>]*href="([^"]+)"', html)
        if not hrefs:
            return
        step = max(1, len(hrefs) // 8)
        sample = hrefs[::step][:8]
        if strict:
            sample = hrefs
        for url in sample:
            try:
                req = urllib.request.Request(url, headers=UA, method="HEAD")
                with urllib.request.urlopen(req, timeout=30) as resp:
                    ctype = resp.headers.get("Content-Type", "")
                if ctype.startswith("text/html"):
                    s.fail(f"vault link serves HTML instead of media: {url[:110]}")
            except Exception as exc:  # noqa: BLE001 - report, keep going
                s.fail(f"vault link unreachable ({exc}): {url[:110]}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run every repository gate")
    ap.add_argument("--manifest", help="local path or URL to the wallpaper assets.json")
    ap.add_argument("--offline", action="store_true", help="skip all network access")
    ap.add_argument("--strict-links", action="store_true", help="probe every outbound link")
    args = ap.parse_args(argv)

    report = Report()
    check_structure(report)
    manifest = load_manifest(args.manifest, args.offline)
    check_vault(report, manifest)
    check_thumbnails(report)
    check_catalogue(report)
    check_versions(report)
    check_html(report)
    check_local_links(report)
    if not args.offline:
        check_remote_links(report, manifest, args.strict_links)

    report.render()
    if report.failed():
        print("\nGate failed.")
        return 1
    print("\nAll gates passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
