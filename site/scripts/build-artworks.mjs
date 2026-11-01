#!/usr/bin/env node
/**
 * build-artworks.mjs — 内容管线（Content Pipeline）
 * ---------------------------------------------------------------
 * 输入：src/data/gallery.json（由壁纸仓 scan 得到的原始清单）
 *      public/thumbs/<category>/<stem>.webp（已提交的 400px 网格缩略图）
 * 输出：src/data/manifest.json（站点唯一数据源）
 *
 * 为每件作品补充：
 *  - slug / title / variant  （文件名规范化 + 人工覆盖 artworks.meta.json）
 *  - theme                   （归属展厅，见 src/data/themes.json）
 *  - dominant                （主色，用于 CSS 占位与卡片描边）
 *  - lqip                    （24px WebP base64 data-URI，消除 CLS / 首屏闪烁）
 *  - thumbW/thumbH           （占位宽高比，避免布局抖动）
 *  - full/fullSrcset         （原图 CDN 地址，wsrv.nl 动态转码 WebP）
 *
 * 幂等：重复执行结果一致（sharp 结果缓存进 .cache/）。
 */
import { readFile, writeFile, mkdir, stat, readdir } from "node:fs/promises"
import { existsSync } from "node:fs"
import path from "node:path"
import crypto from "node:crypto"

const ROOT = process.cwd()
const SRC_JSON = path.join(ROOT, "src/data/gallery.json")
const META_JSON = path.join(ROOT, "src/data/artworks.meta.json")
const THEMES_JSON = path.join(ROOT, "src/data/themes.json")
const OUT_JSON = path.join(ROOT, "src/data/manifest.json")
const THUMB_ROOT = path.join(ROOT, "public/thumbs")
const CACHE_DIR = path.join(ROOT, ".cache/lqip")

// 原图 CDN：GitHub raw 作为唯一来源，wsrv.nl 负责按需转码
const RAW_BASE = "https://raw.githubusercontent.com/Nailong-Studio/NaiWa-Wallpaper/main"
const CDN_BASE = "https://wsrv.nl/"
const CDN_WIDTHS = [640, 1024, 1600, 2048]

/** 文件名 → 标题 / 变体 */
function normalizeName(file) {
  const stem = file.replace(/\.[^.]+$/, "")
  const m = stem.match(/^(.*?)[_-](\d+(?:\.\d+)?s?)$/i)
  let base = stem
  let variant = ""
  if (m && m[1]) {
    base = m[1]
    variant = m[2]
  }
  const hasCJK = /[\u4e00-\u9fff]/.test(base)
  let title = base.replace(/_/g, " ").trim()
  if (!hasCJK) {
    title = title
      .replace(/[-]+/g, " ")
      .replace(/\s+/g, " ")
      .trim()
      .replace(/\b\w/g, (c) => c.toUpperCase())
      .replace(/Nailoong/g, "NaiLoong")
  }
  return { title: title || stem, variant, stem }
}

function slugify(stem) {
  // 保留 CJK 与字母数字；其余折叠为 -
  return encodeURIComponent(
    stem
      .toLowerCase()
      .replace(/[^\p{Script=Han}\w\s-]/gu, "")
      .trim()
      .replace(/\s+/g, "-")
  )
}

function cdnUrl(srcPath, w) {
  const raw = `${RAW_BASE}/${srcPath}`
  const qs = new URLSearchParams({ url: raw.replace(/^https?:\/\//, ""), w: String(w), output: "webp", q: "82" })
  return `${CDN_BASE}?${qs.toString()}`
}

/** 原分辨率展示图：不传 w，保持图片原始像素，仅转码 WebP（q82，接近无损但体积仅为 PNG 1/10 左右） */
function cdnFullUrl(srcPath) {
  const raw = `${RAW_BASE}/${srcPath}`
  const qs = new URLSearchParams({ url: raw.replace(/^https?:\/\//, ""), output: "webp", q: "82" })
  return `${CDN_BASE}?${qs.toString()}`
}

async function lqipFor(thumbAbs, key) {
  await mkdir(CACHE_DIR, { recursive: true })
  const cacheFile = path.join(CACHE_DIR, `${key}.json`)
  if (existsSync(cacheFile)) return JSON.parse(await readFile(cacheFile, "utf8"))
  const sharp = (await import("sharp")).default
  const buf = await readFile(thumbAbs)
  const img = sharp(buf)
  const meta = await img.metadata()
  const { dominant } = meta
  const small = await sharp(buf).resize({ width: 24 }).webp({ quality: 30 }).toBuffer()
  const out = {
    lqip: `data:image/webp;base64,${small.toString("base64")}`,
    dominant: dominant ? rgbHex(dominant) : "#1b1b1b",
  }
  await writeFile(cacheFile, JSON.stringify(out))
  return out
}

function rgbHex({ r, g, b }) {
  const h = (n) => n.toString(16).padStart(2, "0")
  return `#${h(r)}${h(g)}${h(b)}`
}

async function main() {
  const gallery = JSON.parse(await readFile(SRC_JSON, "utf8"))
  const themes = JSON.parse(await readFile(THEMES_JSON, "utf8"))
  const overrides = existsSync(META_JSON) ? JSON.parse(await readFile(META_JSON, "utf8")) : {}
  const themeByCat = Object.fromEntries(themes.map((t) => [t.category, t.id]))

  const items = []
  let missingThumb = 0
  for (const g of gallery) {
    const thumbAbs = path.join(ROOT, "public", g.thumb)
    if (!existsSync(thumbAbs)) {
      missingThumb++
      continue
    }
    const { title, variant, stem } = normalizeName(g.file)
    const key = crypto.createHash("sha1").update(g.thumb).digest("hex").slice(0, 16)
    const { lqip, dominant } = await lqipFor(thumbAbs, key)
    const ov = overrides[g.id] ?? {}
    items.push({
      id: g.id,
      slug: ov.slug ?? slugify(stem),
      category: g.category,
      theme: ov.theme ?? themeByCat[g.category] ?? g.category,
      file: g.file,
      title: ov.title ?? title,
      variant,
      story: ov.story ?? "",
      tags: ov.tags ?? [],
      src: g.src,
      thumb: g.thumb,
      // 原始文件（GitHub raw，6–10MB，仅用于"原始文件"下载入口）
      full: `${RAW_BASE}/${g.src.replace(/^wallpapers\//, "")}`,
      // 展示用大图：原分辨率 WebP（保持原始像素，画质接近原图）
      view: cdnFullUrl(g.src.replace(/^wallpapers\//, "")),
      // srcset：覆盖小到大各档位，最高档 = 原图宽度，浏览器按容器挑最清晰档
      fullSrcset: [...CDN_WIDTHS, g.w].filter((w, i, a) => a.indexOf(w) === i).map((w) => `${cdnUrl(g.src.replace(/^wallpapers\//, ""), w)} ${w}w`).join(", "),
      w: g.w,
      h: g.h,
      size: g.size,
      dominant,
      lqip,
    })
  }

  items.sort((a, b) => (a.category === b.category ? a.file.localeCompare(b.file, "zh") : themes.findIndex((t) => t.category === a.category) - themes.findIndex((t) => t.category === b.category)))

  const payload = {
    generatedAt: new Date().toISOString(),
    count: items.length,
    themes,
    categories: themes.map((t) => ({ ...t, count: items.filter((i) => i.category === t.category).length })),
    items,
  }
  await writeFile(OUT_JSON, JSON.stringify(payload, null, 2), "utf8")
  const onDisk = (await readdir(THUMB_ROOT, { withFileTypes: true })).length
  console.log(`✔ manifest: ${items.length} 件作品 · ${payload.categories.length} 个展厅 · 缩略图目录 ${onDisk} 个子目录`)
  if (missingThumb) console.warn(`⚠ 跳过 ${missingThumb} 条（缩略图缺失）`)
}

main().catch((e) => {
  console.error("✖ build-artworks 失败:", e.message)
  process.exit(1)
})
