# NaiLoong Style Guide · 奶龙样式指南

对标 `catppuccin/docs/style-guide.md`，所有 Port 必须从 `palette.json` 单源生成。

## 调色板

- 单源：`palette.json` `version 1.0.0`，双口味 `nailoongDark` / `nailoongLight` 各 26 色
- 主色：`milkYellow #FFD54F` / `#F9A825`（奶黄），眼睛 `eyeGreen #66BB6A` / `#2E7D32` 点睛
- 基底：`base #121212` / `mantle #0F0F0F` / `crust #0A0A0A` 暖黑，`surface0 #1F1A0F` / `surface1 #2E2511` 暖棕
- 灰阶：`overlay0 #7A6F5A` / `overlay1 #8A7A5A` / `overlay2 #9C8E7A` 暖灰
- 语义：`red #E57373` 错误，`blue #4FC3F7` 函数，`mauve #BA68C8` 变量，`cyan #4DD0E1` 属性

见 `palette.json` 完整 26 色，`hsl` 已计算，新增色需按 `order` 排序并同时提供 Dark/Light。

## 口味

| 口味 | 类型 | 用途 |
| --- | --- | --- |
| `nailoongDark` | `vs-dark` | 默认，暖黑底 + 奶黄高亮 + 绿光标 |
| `nailoongLight` | `vs` | 暖白底 + 深奶黄高亮 + 绿光标 |

## 生成

```bash
# 生成全部 Port（对比 catppuccin 的 pnpm generate）
python3 scripts/generate.py --all
python3 scripts/generate.py --port terminal
python3 scripts/generate.py --port vscode-theme

# 校验
python3 scripts/generate.py --check
```

`scripts/generate.py` 读取 `palette.json` 输出到：
- `themes/terminal/*.json` / `*.itermcolors`
- `themes/windows/NaiLoong.theme`
- 也可为 `themes/vscode/` 生成 VS Code 主题 `themes/*.json`

## Port 规范

- 一工具一仓：参考 `resources/ports.yml`
- 新 Port 需在 `resources/ports.yml` 注册，并提供 `README` + 安装说明
- 禁止硬编码色值，必须从 `palette.json` 引用（`scripts/generate.py` 会校验）
- 提交前 `python3 scripts/generate.py --check` 保证与单源一致

## 版本

- `palette.json` 版本与 `VERSION` 同步，改色必须 bump `1.0.0` → `1.1.0` 并同步 `CHANGELOG`
