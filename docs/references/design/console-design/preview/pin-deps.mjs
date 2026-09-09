// pin-deps.mjs — 参考预览依赖固定脚本（PLAN-20260908-034 T01）
//
// 目的：把设计原型 HTML 中引用的 CDN 依赖（React/ReactDOM/Babel UMD、
// Google Fonts）下载为本地文件并校验完整性，使参考预览可离线、可复现。
// 本脚本只影响 docs/references/design/console-design/preview/，
// 不进入产品构建，不修改上游原型。
//
// 用法：node pin-deps.mjs
// 幂等：vendor/ 与 fonts/ 已存在且 digest 匹配时跳过下载。

import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile, readdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));

/** 与 App.html 中 integrity 属性一致的 SRI（sha384）。 */
const VENDOR = [
  {
    file: "react.development.js",
    url: "https://unpkg.com/react@18.3.1/umd/react.development.js",
    sri: "sha384-hD6/rw4ppMLGNu3tX5cjIb+uRZ7UkRJ6BPkLpg4hAu/6onKUg4lLsHAs9EBPT82L",
  },
  {
    file: "react-dom.development.js",
    url: "https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js",
    sri: "sha384-u6aeetuaXnQ38mYT8rp6sbXaQe3NL9t+IBXmnYxwkUI2Hw4bsp2Wvmx4yRQF1uAm",
  },
  {
    file: "babel.min.js",
    url: "https://unpkg.com/@babel/standalone@7.29.0/babel.min.js",
    sri: "sha384-m08KidiNqLdpJqLq95G/LEi8Qvjl/xUYll3QILypMoQ65QorJ9Lvtp2RXYGBFj1y",
  },
];

const FONT_CSS_URL =
  "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap";
// 现代浏览器 UA，确保 Google Fonts 返回 woff2 格式。
const FONT_UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36";

function sriOf(buf, algo) {
  return `${algo}-${createHash(algo).update(buf).digest("base64")}`;
}

async function download(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`fetch ${url} -> ${res.status}`);
  return Buffer.from(await res.arrayBuffer());
}

async function ensureVendor() {
  const dir = path.join(HERE, "vendor");
  await mkdir(dir, { recursive: true });
  const manifest = [];
  for (const v of VENDOR) {
    const target = path.join(dir, v.file);
    let buf;
    try {
      buf = await readFile(target);
      if (sriOf(buf, "sha384") !== v.sri) throw new Error("digest mismatch on cached file");
    } catch {
      buf = await download(v.url);
      if (sriOf(buf, "sha384") !== v.sri) {
        throw new Error(`SRI verification failed for ${v.url}`);
      }
      await writeFile(target, buf);
    }
    manifest.push({ file: `vendor/${v.file}`, url: v.url, sri: v.sri, sha256: sriOf(buf, "sha256"), bytes: buf.length });
  }
  return manifest;
}

async function ensureFonts() {
  const dir = path.join(HERE, "fonts");
  await mkdir(dir, { recursive: true });
  const cssTarget = path.join(dir, "fonts.css");
  try {
    await readFile(cssTarget);
    return; // 已固定
  } catch {
    /* 首次下载 */
  }
  const res = await fetch(FONT_CSS_URL, { headers: { "User-Agent": FONT_UA } });
  if (!res.ok) throw new Error(`font css -> ${res.status}`);
  let css = await res.text();
  const urls = [...css.matchAll(/url\((https:[^)]+)\)/g)].map((m) => m[1]);
  const unique = [...new Set(urls)];
  for (const url of unique) {
    const buf = await download(url);
    const name = `${sriOf(buf, "sha256").slice(7, 23).replace(/[^A-Za-z0-9]/g, "_")}.woff2`;
    await writeFile(path.join(dir, name), buf);
    css = css.split(url).join(name);
  }
  await writeFile(cssTarget, css);
}

async function rewriteHtml() {
  const htmls = ["App.html", "Overview.html", "Command Center.html"];
  for (const name of htmls) {
    const target = path.join(HERE, name);
    let html = await readFile(target, "utf8");
    for (const v of VENDOR) {
      html = html.split(v.url).join(`vendor/${v.file}`);
    }
    html = html
      .split("https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap")
      .join("fonts/fonts.css");
    html = html.split('<link rel="preconnect" href="https://fonts.googleapis.com"/>').join("");
    html = html.split('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>').join("");
    // 移除本地文件的 SRI/crossorigin（file 同源无需）
    await writeFile(target, html);
  }
}

const manifest = await (async () => {
  const vendor = await ensureVendor();
  await ensureFonts();
  await rewriteHtml();
  const fonts = (await readdir(path.join(HERE, "fonts"))).filter((f) => f.endsWith(".woff2"));
  return { vendor, fontFiles: fonts.length, fontsCss: "fonts/fonts.css" };
})();

console.log(JSON.stringify(manifest, null, 2));
