#!/usr/bin/env python3
"""NaiLoong palette 单源生成器 - 对标 catppuccin/resources/generate/main.ts
用法:
  python3 scripts/generate.py --all
  python3 scripts/generate.py --port terminal
  python3 scripts/generate.py --check
从 palette.json 读取 nailoongDark 口味生成各 Port 配置。
原则：只改 palette.json，此脚本输出即为真值，禁止手改 themes/。
"""
import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PALETTE_PATH = ROOT / "palette.json"


def load_palette():
    data = json.loads(PALETTE_PATH.read_text(encoding="utf-8"))
    dark = data["nailoongDark"]["colors"]
    light = data["nailoongLight"]["colors"]
    return data, dark, light


def hex_to_rgb_str(hexc):
    hexc = hexc.lstrip("#")
    return f"{int(hexc[0:2],16)} {int(hexc[2:4],16)} {int(hexc[4:6],16)}"


def render_terminal():
    """按 palette.json 渲染终端三件套 + Windows 主题，返回 {相对路径: 内容}"""
    _, dark, _ = load_palette()
    rendered = {}

    vscode = {
        "$schema": "vscode://schemas/workbench.json",
        "workbench.colorCustomizations": {
            "terminal.background": dark["base"]["hex"],
            "terminal.foreground": dark["text"]["hex"],
            "terminalCursor.background": dark["base"]["hex"],
            "terminalCursor.foreground": dark["eyeGreen"]["hex"],
            "terminal.selectionBackground": dark["surface1"]["hex"],
            "terminal.ansiBlack": dark["base"]["hex"],
            "terminal.ansiRed": dark["red"]["hex"],
            "terminal.ansiGreen": dark["eyeGreen"]["hex"],
            "terminal.ansiYellow": dark["milkYellow"]["hex"],
            "terminal.ansiBlue": dark["blue"]["hex"],
            "terminal.ansiMagenta": dark["mauve"]["hex"],
            "terminal.ansiCyan": dark["cyan"]["hex"],
            "terminal.ansiWhite": dark["text"]["hex"],
            "terminal.ansiBrightBlack": dark["overlay1"]["hex"],
            "terminal.ansiBrightRed": dark["redLight"]["hex"],
            "terminal.ansiBrightGreen": dark["eyeGreenLight"]["hex"],
            "terminal.ansiBrightYellow": dark["milkYellowLight"]["hex"],
            "terminal.ansiBrightBlue": dark["blueLight"]["hex"],
            "terminal.ansiBrightMagenta": dark["mauveLight"]["hex"],
            "terminal.ansiBrightCyan": dark["cyanLight"]["hex"],
            "terminal.ansiBrightWhite": dark["text"]["hex"],
        },
    }
    rendered["themes/terminal/nailoong-vscode-terminal.json"] = (
        json.dumps(vscode, indent=2, ensure_ascii=False) + "\n"
    )

    wt = {
        "name": "NaiLoong",
        "foreground": dark["text"]["hex"],
        "background": dark["base"]["hex"],
        "cursorColor": dark["eyeGreen"]["hex"],
        "selectionBackground": dark["surface1"]["hex"],
        "colors": {
            "black": dark["base"]["hex"],
            "red": dark["red"]["hex"],
            "green": dark["eyeGreen"]["hex"],
            "yellow": dark["milkYellow"]["hex"],
            "blue": dark["blue"]["hex"],
            "purple": dark["mauve"]["hex"],
            "cyan": dark["cyan"]["hex"],
            "white": dark["text"]["hex"],
            "brightBlack": dark["overlay1"]["hex"],
            "brightRed": dark["redLight"]["hex"],
            "brightGreen": dark["eyeGreenLight"]["hex"],
            "brightYellow": dark["milkYellowLight"]["hex"],
            "brightBlue": dark["blueLight"]["hex"],
            "brightPurple": dark["mauveLight"]["hex"],
            "brightCyan": dark["cyanLight"]["hex"],
            "brightWhite": dark["text"]["hex"],
        },
    }
    rendered["themes/terminal/windows-terminal.json"] = (
        json.dumps(wt, indent=2, ensure_ascii=False) + "\n"
    )

    win_content = f"""; NaiLoong.theme - 奶龙 Windows 主题示例
; 用法：复制到 C:\\Windows\\Resources\\Themes 后双击应用
; 由 palette.json 单源生成，请勿手改
[Theme]
DisplayName=NaiLoong (奶龙主题)
ThemeId={{8A1B2C3D-4E5F-6A7B-8C9D-0E1F2A3B4C5D}}

[Control Panel\\Desktop]
Wallpaper=%SystemRoot%\\Resources\\Themes\\NaiLoong\\wallpapers\\nai-long-sleeping-01.png
TileWallpaper=0
WallpaperStyle=10

[Control Panel\\Colors]
Background={hex_to_rgb_str(dark['base']['hex'])}
Window={hex_to_rgb_str(dark['base']['hex'])}
WindowText={hex_to_rgb_str(dark['text']['hex'])}
ActiveTitle={hex_to_rgb_str(dark['milkYellow']['hex'])}
InactiveTitle={hex_to_rgb_str(dark['surface1']['hex'])}
Menu={hex_to_rgb_str(dark['base']['hex'])}
MenuText={hex_to_rgb_str(dark['text']['hex'])}
ButtonFace={hex_to_rgb_str(dark['base']['hex'])}
ButtonText={hex_to_rgb_str(dark['text']['hex'])}
Highlight={hex_to_rgb_str(dark['milkYellow']['hex'])}
HighlightText={hex_to_rgb_str(dark['base']['hex'])}
"""
    rendered["themes/windows/NaiLoong.theme"] = win_content
    return rendered


def generate():
    rendered = render_terminal()
    for rel, content in rendered.items():
        p = ROOT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        print(f"generated {p}")


def check():
    print("check: verifying generated files match palette.json...")
    rendered = render_terminal()
    mismatches = []
    for rel, expected in rendered.items():
        p = ROOT / rel
        actual = p.read_text(encoding="utf-8") if p.exists() else ""
        if actual != expected:
            mismatches.append(rel)
    if mismatches:
        print(f"mismatch: {', '.join(mismatches)}")
        print("run: python3 scripts/generate.py --all")
        sys.exit(1)
    print("check passed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="生成全部")
    parser.add_argument("--check", action="store_true", help="校验是否与单源一致")
    args = parser.parse_args()
    if args.check:
        check()
    elif args.all or len(sys.argv) == 1:
        generate()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
