#!/usr/bin/env python3
"""从 docs/index.html 抽取藏品元数据，生成 docs/data/collection.json，并做一致性校验。

用法：
    python scripts/export_collection.py            # 导出 + 基础校验
    python scripts/export_collection.py --check    # 仅校验（含素材仓外链，需网络）
"""
import json
import os
import re
import sys
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "docs", "index.html")
OUT = os.path.join(ROOT, "docs", "data", "collection.json")
BAD_NAMES = ["奶娃", "奶破龙", "以利龙", "丘比龙", "普绪龙"]

# Halls the museum must keep, and the invariants that must survive a rebuild.
EXPECTED_HALLS = 8


def hall_name_map(html):
    out = {}
    for m in re.finditer(r'<section class="hall[^"]*" id="(hall-\d)"[^>]*>(.*?)<div class="hall__track">', html, flags=re.S):
        hid = m.group(1)
        name = re.search(r'class="hall__name">([^<]+)<', m.group(2))
        desc = re.search(r'class="hall__desc">([^<]+)<', m.group(2))
        out[hid] = {
            "name": name.group(1).replace(" ", "").strip() if name else "",
            "desc": desc.group(1).strip() if desc else "",
        }
    return out


def collect():
    html = open(HTML, encoding="utf-8").read()
    halls = hall_name_map(html)
    items = []
    seq = {}
    for m in re.finditer(r'<section class="hall[^"]*" id="(hall-\d)"[^>]*>.*?(?=<section class="hall[^"]*" id="hall-|<!-- =)', html, flags=re.S):
        hid = m.group(1)
        block = m.group(0)
        for f in re.finditer(r'<figure class="work[^"]*">(.*?)</figure>', block, flags=re.S):
            fig = f.group(1)
            media = re.search(r'<(img|video)\b([^>]*?)>', fig, flags=re.S)
            if not media:
                continue
            tag, attrs = media.group(1), media.group(2)

            def attr(key):
                mm = re.search(key + r'="([^"]*)"', attrs)
                return mm.group(1) if mm else ""

            title = attr("data-title")
            if not title:
                continue
            seq[hid] = seq.get(hid, 0) + 1
            src = attr("src") or attr("poster")
            raw = attr("data-original")
            kind = "video" if tag == "video" else ("gif" if src.lower().endswith(".gif") else "image")
            items.append({
                "id": "NW-%s-%03d" % (hid.replace("hall-", ""), seq[hid]),
                "hall": hid,
                "hallName": halls.get(hid, {}).get("name", ""),
                "title": title,
                "narrative": attr("data-narrative"),
                "asset": src,
                "type": kind,
                "original": raw,
            })
    return html, halls, items


def check(html, items, online=False):
    problems = []
    # The catalogue grows as the warehouse grows, so the count is not pinned to
    # a literal: it must merely be non-empty and free of duplicate ids.
    if not items:
        problems.append("藏品件数为 0")
    ids = [i["id"] for i in items]
    if len(ids) != len(set(ids)):
        dupes = sorted({x for x in ids if ids.count(x) > 1})
        problems.append("藏品编号重复：%s" % ", ".join(dupes[:5]))
    hall_ids = sorted({i["hall"] for i in items})
    if len(hall_ids) != EXPECTED_HALLS:
        problems.append("展厅数应为 %d，实际 %d" % (EXPECTED_HALLS, len(hall_ids)))
    for i in items:
        blob = i["title"] + i["narrative"]
        for bad in BAD_NAMES:
            if bad in blob:
                problems.append("%s 残留旧命名「%s」" % (i["id"], bad))
        if not i["narrative"]:
            problems.append("%s 缺叙事" % i["id"])
    # 素材外链：仅校验 raw.githubusercontent 链接
    if online:
        import urllib.request
        cache = {}
        for i in items:
            raw = i["original"]
            if not raw.startswith("https://raw.githubusercontent.com"):
                continue
            d, f = urllib.parse.unquote(raw.split("/main/")[-1]).split("/", 1)
            if d not in cache:
                url = "https://api.github.com/repos/Nailong-Studio/NaiWa-Wallpaper/contents/" + d
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "nw-check"})
                    cache[d] = [e["name"] for e in json.load(urllib.request.urlopen(req, timeout=40))]
                except Exception as e:
                    problems.append("素材仓目录读取失败 %s: %s" % (d, e))
                    continue
            if f not in cache[d]:
                problems.append("%s 原作链接失效：%s/%s" % (i["id"], d, f))
    return problems


def main():
    html, halls, items = collect()
    online = "--check" in sys.argv
    problems = check(html, items, online)
    if not online:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        payload = {
            "generatedBy": "scripts/export_collection.py",
            "source": "docs/index.html",
            "total": len(items),
            "halls": [{"id": k, **v, "count": sum(1 for i in items if i["hall"] == k)} for k, v in sorted(halls.items())],
            "items": items,
        }
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=1)
        print("已导出 %d 件 → %s" % (len(items), os.path.relpath(OUT, ROOT)))
    for h in sorted(halls):
        c = sum(1 for i in items if i["hall"] == h)
        print("  %s %s：%d 件" % (h, halls[h]["name"], c))
    if problems:
        print("\n发现 %d 个问题：" % len(problems))
        for p in problems[:30]:
            print("  -", p)
        return 1
    print("\n校验通过：件数 / 厅数 / 命名 / 叙事" + (" / 原作外链" if online else "（外链需 --check）"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
