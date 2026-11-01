#!/usr/bin/env python3
"""NaiLoong palette 单源校验 - NaiLoong VS Code 主题（位于主仓 themes/vscode/）
用法: python3 themes/vscode/scripts/generate.py --check
对比主仓根目录 palette.json 关键色与 themes/*.json 是否一致。
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PALETTE_PATH = ROOT.parent.parent / "palette.json"

# palette 色名 -> 主题 colors 键
DARK_MAP = {
    "base": "editor.background",
    "text": "editor.foreground",
    "milkYellow": "activityBar.foreground",
    "eyeGreen": "editorCursor.foreground",
    "surface1": "editor.lineHighlightBackground",
}
LIGHT_MAP = {
    "base": "editor.background",
    "text": "editor.foreground",
    "milkYellow": "activityBar.foreground",
    "eyeGreen": "editorCursor.foreground",
}


def load_palette():
    data = json.loads(PALETTE_PATH.read_text(encoding="utf-8"))
    return data["nailoongDark"]["colors"], data["nailoongLight"]["colors"]


def check_theme(path, palette, mapping):
    theme = json.loads(path.read_text(encoding="utf-8"))
    colors = theme["colors"]
    problems = []
    for color_name, theme_key in mapping.items():
        expected = palette[color_name]["hex"]
        actual = colors.get(theme_key)
        if actual != expected:
            problems.append(f"{theme_key}: expected {expected} got {actual}")
    return problems


def main():
    dark, light = load_palette()
    problems = []
    for rel, palette, mapping in (
        ("themes/NaiLoong-Dark.json", dark, DARK_MAP),
        ("themes/NaiLoong-Light.json", light, LIGHT_MAP),
    ):
        p = ROOT / rel
        if not p.exists():
            print(f"missing: {rel}")
            problems.append(rel)
            continue
        for prob in check_theme(p, palette, mapping):
            problems.append(f"{rel}: {prob}")
    if problems:
        print("mismatch:")
        for prob in problems:
            print(f"  {prob}")
        print("fix: 改主仓根目录 palette.json 后运行 scripts/generate.py --all 与 themes/vscode/scripts/generate.py --check，勿直接手改 themes/")
        sys.exit(1)
    print("check passed: themes/*.json match palette.json")


if __name__ == "__main__":
    main()
