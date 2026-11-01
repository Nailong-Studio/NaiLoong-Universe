# 终端配色

奶龙主题终端配色方案，支持主流终端和编辑器终端。

## 支持的终端

| 终端 | 文件 | 说明 |
| --- | --- | --- |
| Windows Terminal | `windows-terminal.json` | 把里面的方案加到 settings.json |
| iTerm2 | `nailoong.itermcolors` | 双击导入，零门槛 |
| VS Code 终端 | `nailoong-vscode-terminal.json` | 合并进你的 settings.json |
| GNOME Terminal | `nailoong.dconf` | dconf 导入（待做，画饼中） |

## 安装

### Windows Terminal

1. 打开 Windows Terminal 设置（Ctrl+,）
2. 在 "配色方案" 中点击"添加"
3. 把 `windows-terminal.json` 里的颜色字段照抄到新方案
4. 在配置文件中选择该配色方案

### iTerm2

双击 `nailoong.itermcolors` 即可自动导入，然后在 "Profiles -> Colors" 里选中它。

### VS Code

把 `nailoong-vscode-terminal.json` 中的 `workbench.colorCustomizations` 合并进你的 `settings.json`，关掉重开终端生效。

## 配色参考

- 背景/前景：暖黑 `#121212` + 奶白 `#E8F5E9`，选区暖棕 `#2E2511`
- 主色：奶黄 `#FFD54F` / `#F9A825`，眼睛绿 `#66BB6A` / `#2E7D32` 点睛（光标/远程/括号匹配）
- 遵循 16 色 ANSI 标准，与 `themes/vscode/` 的 NaiLoong Dark/Light 对齐，兼容大部分终端

## 贡献

新增终端支持时，请保持色值与其他文件一致，并更新本表。
