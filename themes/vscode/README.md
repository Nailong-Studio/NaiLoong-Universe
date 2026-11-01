# NaiLoong VS Code Theme · 奶蛙 VS Code 主题

> 把 VS Code 变成奶蛙的窝。**奶黄 `#FFD54F` 为主色 + 绿色 `#66BB6A` 点睛（两只绿眼睛）**，暖黑护眼底。

本目录是奶蛙主题包的 VS Code 主题包（原独立仓库 `nailoong-vscode-theme` 已并入主仓）。色值来自主仓根目录 **`palette.json` 单源**，勿手改主题文件——改色去主仓改 `palette.json` 后重新生成。

## 主题一览

| 主题 | 类型 | 适合 |
| --- | --- | --- |
| **NaiLoong Dark** | `vs-dark` | 暖黑底 + 奶黄高亮，默认推荐 |
| **NaiLoong Light** | `vs` | 暖白底 + 深奶黄，日间明亮 |

## 调色板单源

- 唯一真源：主仓根目录 `palette.json`（`nailoongDark`/`nailoongLight` 各 26 色）
- 主色：`milkYellow #FFD54F` / `#F9A825`（奶黄）
- 眼睛：`eyeGreen #66BB6A` / `#2E7D32`（绿光标 / 远程角标 / 括号匹配 / 终端绿）
- 基底：`base #121212`（暖黑）、`surface1 #2E2511`（暖棕选中）
- 重新生成主题（改色后用）：

```bash
python3 scripts/generate.py --all          # 主仓：生成终端/Windows 主题
python3 themes/vscode/scripts/generate.py --check  # 校验 VS Code 主题与 palette 一致
```

> 改色流程：改主仓根目录 `palette.json` → 跑上面两条命令 → 提交。

## 预览

- Editor：暖黑底 + 奶白字 + **绿光标（眼睛）**
- ActivityBar / Tab / Button 奶黄高亮，`statusBar` 深奶黄褐 `#2A1F0A` + 黄边框
- Terminal 16 色与 `themes/terminal/` 的 `nailoong-vscode-terminal.json` / `nailoong.itermcolors` / `windows-terminal.json` 三件套一致
- Token：注释暖灰斜体、字符串奶黄、关键字红、函数天空蓝

## 安装

### 插件市场（待发布）

```bash
code --install-extension Nailong-Studio.nailoong-vscode-theme
```

### 本地打包 / 预览

```bash
# 方式1：直接安装 vsix
npx @vscode/vsce package
code --install-extension nailoong-vscode-theme-1.0.0.vsix

# 方式2：开发模式
code --extensionDevelopmentPath=<主仓路径>/themes/vscode
```

然后 `Ctrl+K Ctrl+T` 选择 `NaiLoong Dark` / `NaiLoong Light`。

## 目录结构

```
themes/vscode/
├── palette.json  → 已删除，唯一真源在主仓根目录
├── themes/NaiLoong-Dark.json / NaiLoong-Light.json
├── package.json  # 发布配置（vsce package）
├── assets/       # 扩展图标
├── scripts/generate.py  # palette 一致性校验
└── .vscodeignore # 打包忽略规则
```
