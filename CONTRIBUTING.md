# 圣殿共建手册 · CONTRIBUTING

**欢迎入殿。** 读完这本手册（约 3 分钟），你就是圣殿的正式编外施工员了。

## 圣殿守则（违反者会被奶蛙瞪三秒）

1. **奶蛙 ≠ 奶龙**：奶蛙是官方奶龙角色的民间 AI 变异体（黄圆润 / 浅米腹 / 绿眼 / 灰爪）。素材与文案只准出现奶蛙；官方奶龙素材需标注来源、尊重版权。
2. **命名统一**：`分类_主题_序号` 中文命名，前缀一律「奶蛙-」。看到 `IMG_0001.png` 或 `milk_frog_v3.png`，请就地劝返。
3. **每件素材必须有叙事**：同名 `.txt`，同目录。写不清"它是谁、在干嘛、为什么好笑"，圣殿不收。
4. **不重复入库**：提交前在素材仓搜关键词 + 像素级对照。两件一模一样的「奶蛙-弯腰大笑」会让圣殿强迫症发作。

## 你能贡献什么（按难易排序）

| 难度 | 贡献 | 说明 |
| --- | --- | --- |
| 1/5 | 提交素材 | 一张奶蛙图 + 一句话叙事，PR 到 [wallpaper](https://github.com/Nailong-Studio/NaiWa-Wallpaper) |
| 2/5 | 写叙事 | 给已有素材配更有梗的 `.txt` |
| 3/5 | 改官网 | `docs/index.html` 是单文件自包含，改完浏览器直接能看 |
| 4/5 | 出新主题 | 读 `palette.json`，派生 Windows / macOS / 终端 / VS Code 主题 |
| 5/5 | 当维护者 | 先贡献 10 次，我们会主动来找你（也可能不找，但你已经是了） |

## 官网怎么改（给想动代码的你）

- 官网是**自包含单文件** `docs/index.html`（CSS/JS 全内联，零构建、零框架、零安装）
- 本地双击就能预览；改完用浏览器 DevTools 确认 console 无报错
- 多「页面」走 hash 路由：`#home` `#halls` `#chronicle` `#visit`
- 新作品插入对应展厅的 `hall__track`，**必须**带 `data-title` / `data-narrative` / `data-hall` / `data-original`
- 资源放 `docs/assets/`，路径写相对路径，只写进 `src` 或 CSS `url()`（发布链只扫这两处，写在别处会裂图，真的会）

## 提交前必须过的门禁

本地跑一次，和 CI 完全等价：

```bash
python scripts/check_site.py --manifest path/to/assets.json
```

全绿再提 PR。它检查图鉴与素材清单是否一致、有没有重复编码的链接、缩略图是否齐全、
藏品索引与展厅数是否自洽、`VERSION` 与 CHANGELOG 与 Service Worker 缓存是否同版本、
HTML 标签是否配平、内联脚本能否解析、本地引用是否存在。红门禁不要靠改检查绕过——改内容。

**图鉴区块是生成物，不要手改。** `scripts/build_vault.py` 是唯一允许写它的程序：

```bash
python scripts/build_vault.py --manifest assets.json              # 重建
python scripts/build_vault.py --manifest assets.json --check      # 只校验
python scripts/build_vault.py --manifest assets.json --fetch-thumbs  # 顺带补齐缩略图
```

手工往图鉴里塞卡片，就是 385 条链接被双重编码的成因。

## 提交流程（PR 礼仪）

1. Fork 本仓库 → 新建分支（`feat/xxx` 或 `fix/xxx`）
2. 提交，commit message 用祈使句说清做了什么（`fix: repair vault original links` 就是模范生）
3. 开 PR 到 `main`，描述里写：改了什么、为什么、素材出处
4. 等审查 → 合并 → GitHub Actions 自动部署官网 → 圣殿换新颜

## 行为准则

参与即代表同意 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)：对所有人友善、尊重版权、不灌水、不搬运无关内容。被指出问题就改，改完还是朋友。

---

**最后一句**：圣殿不缺代码，缺的是快乐。你每提交一件素材，就有一张桌子上的聊天多一个笑点——这比任何 Star 都值（但 Star 也请顺手点一下）。
