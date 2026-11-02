/**
 * 后端路由必须**要么有前端消费者，要么被如实登记**（GOAL-20261103-104 EC-04）。
 *
 * **补的是哪一格**：`docs/api/openapi.m13.json` 是后端路由的唯一权威，而前端有没有人调它
 * **没有任何机械判据**。2026-11-03 实测：132 条路由里 10 条完全没有消费者，其中 7 条
 * （评审判词 / 研究方向 / 研究程序四条）是用户真的会问「为什么页面上看不到」的面 ——
 * 缺口靠人肉 grep 才发现。
 *
 * 判据是**两选一**，且第二个选项不是免罪符：
 * - 有消费者：`apps/web/src/api/*.ts` 里有请求路径与它同形；
 * - **或者**在 `docs/frontend/UNCONSUMED.md` 的白名单里，且**每条必须带理由**。
 *
 * **为什么允许白名单**：不是每条后端路由都该有 UI（`/health` 是探针、`/cost/daily` 是
 * 运维端点）。把这些硬塞进界面 = 造没有需求的页面。白名单让「暂不暴露」成为一份**可审计
 * 的决定**，而不是一个没人查的空白。
 *
 * **路径同形的三条规则**（每一 条都来自实测的假阴性）：
 * 1. `{param}` 与 `${...}` 都归一成 `{p}`；
 * 2. **一跳可达**：`request(packPath(id, "revoke"))` 这类经局部 helper 拼出来的路径也是
 *    消费者 —— 只认同文件内的字面量会把 12 条已经接好线的路由判成「无消费者」；
 * 3. 查询串（`?kind=` / `${suffix}`）不参与比较：它不是路由身份。
 */

import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

import { readWhitelist } from "./unconsumed-registry";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "../../../..");
const OPENAPI = path.join(ROOT, "docs/api/openapi.m13.json");
const CLIENT_DIR = path.join(ROOT, "apps/web/src/api");

const METHODS = new Set(["get", "post", "put", "patch", "delete"]);

interface Route {
  method: string;
  path: string;
}

function openapiRoutes(): Route[] {
  const doc = JSON.parse(readFileSync(OPENAPI, "utf8")) as {
    paths: Record<string, Record<string, unknown>>;
  };
  const routes: Route[] = [];
  for (const [routePath, ops] of Object.entries(doc.paths)) {
    for (const method of Object.keys(ops)) {
      if (METHODS.has(method.toLowerCase())) {
        routes.push({ method: method.toUpperCase(), path: routePath });
      }
    }
  }
  return routes;
}

/**
 * 路由身份：`{param}` 与 `${...}` 一律折成 `{p}`，查询串丢弃。
 *
 * **查询串的两种写法都要认**：`?kind=x` 与 `${suffix}` 拼在路径尾部。后者归一后是
 * `/cost/daily{p}` —— 尾部 `{p}` 前面**不是** `/` ⇒ 它不是路径段而是查询串，去掉。
 * 反之 `/tool-packs/{p}/{p}` 尾部的 `{p}` 前面是 `/` ⇒ 它是真路径段，必须保留。
 */
export function shape(raw: string): string {
  const withoutQuery = raw.split("?")[0] ?? "";
  const folded = withoutQuery
    .replace(/\$\{[^}]*\}/g, "{p}")
    .replace(/\{[^}]+\}/g, "{p}")
    .replace(/\/+$/, "");
  const trail = folded.endsWith("{p}") ? folded.slice(0, -"{p}".length) : "";
  if (trail !== "" && !trail.endsWith("/")) {
    return trail; // `${suffix}` 形态的查询串
  }
  return folded;
}

/**
 * 一个 client 模块里**所有**可能的路径形状。
 *
 * 取**每一个含 `/` 的字符串/模板字面量**（不要求以 `/` 开头）—— 经 helper 拼出来的路径
 * 往往以插值起头（`${API_BASE}/artifacts/…`、`${base}/${action}`），只认以 `/` 开头的
 * 字面量会把**已经接好线**的路由判成「无消费者」，逼出假白名单条目。
 *
 * 拼装面覆盖三种真实写法（每一种都实测撞过）：
 * 1. **`${API_BASE}/x`** ⇒ 前导插值是 `/api` 前缀，去掉即得路由身份；
 * 2. **`${base}/${action}`** ⇒ 后缀片段要与同模块的**前缀字面量**组合
 *    （`const base = "/tool-provider-registrations/${id}"` 是前缀）；
 * 3. **动作名当参数** ⇒ 尾部 `{p}` 用同模块出现的**短字面量**逐一填（`"approve"` /
 *    `"health-check"` / `"revoke"`）。
 *
 * 三条都只放宽「参数/前缀从哪来」，**没有**放宽「路径必须有人拼出来」。
 */
/** 一个模块里出现的**短字面量**（动作名候选：`"approve"` / `"health-check"` / `"revoke"`）。 */
function shortWords(text: string): string[] {
  return [...text.matchAll(/[`"']([A-Za-z][\w-]*)[`"']/g)]
    .map((match) => match[1] ?? "")
    .filter((word) => word !== "");
}

const SKIP_FILES = new Set(["types.ts", "problemText.ts", "http.ts", "legacyShapes.ts"]);

/** 含 `/` 的字符串/模板字面量（引号三种都认；不跨行）。 */
const LITERAL_WITH_SLASH = /[`"']([^`"'\n]*\/[^`"'\n]*)[`"']/g;

interface LiteralScan {
  prefixes: string[];
  suffixes: string[];
}

/** 把模块里的字面量分成「前缀」与「后缀」两类（后缀 = 以插值起头的模板）。 */
function scanLiterals(text: string): LiteralScan {
  const prefixes: string[] = [];
  const suffixes: string[] = [];
  for (const match of text.matchAll(LITERAL_WITH_SLASH)) {
    const literal = match[1] ?? "";
    if (!literal.startsWith("/") && !literal.includes("${")) continue;
    const folded = shape(literal);
    if (folded.startsWith("/")) prefixes.push(folded);
    else if (folded.startsWith("{p}/")) suffixes.push(folded.slice("{p}/".length));
  }
  return { prefixes, suffixes };
}

/** 尾部 `{p}` 是 helper 的动作参数 ⇒ 用同模块短字面量填（`/tool-packs/{p}/approve`）。 */
function fillTrailingParam(prefix: string, words: string[]): string[] {
  if (!prefix.endsWith("{p}")) return [];
  const stem = prefix.slice(0, -"{p}".length);
  return words.map((word) => shape(`${stem}${word}`));
}

/** 前缀 × 后缀的组合（含把后缀里的 `{p}` 用短字面量填一次）。 */
function combine(prefix: string, suffix: string, words: string[]): string[] {
  const filled = words.map((word) => shape(`${prefix}/${suffix.replace("{p}", word)}`));
  return [shape(`${prefix}/${suffix}`), ...filled];
}

function moduleShapes(text: string): string[] {
  const words = shortWords(text);
  const { prefixes, suffixes } = scanLiterals(text);
  const out = new Set<string>(prefixes);
  for (const prefix of prefixes) {
    for (const filled of fillTrailingParam(prefix, words)) out.add(filled);
    for (const suffix of suffixes) {
      for (const combined of combine(prefix, suffix, words)) out.add(combined);
    }
  }
  for (const suffix of suffixes) out.add(shape(`/${suffix}`));
  return [...out];
}

function clientShapes(): Set<string> {
  const shapes = new Set<string>();
  for (const name of clientFiles()) {
    const text = readFileSync(path.join(CLIENT_DIR, name), "utf8");
    for (const folded of moduleShapes(text)) shapes.add(folded);
  }
  return shapes;
}

function clientFiles(): string[] {
  return readdirSync(CLIENT_DIR)
    .filter((name) => name.endsWith(".ts") && !SKIP_FILES.has(name))
    .sort();
}

test("every OpenAPI route has a frontend consumer or a reasoned whitelist entry", () => {
  const routes = openapiRoutes();
  assert.ok(routes.length > 100, `only ${String(routes.length)} routes parsed from OpenAPI`);
  const shapes = clientShapes();
  const listed = readWhitelist();
  const allowed = new Set(listed.map((entry) => `${entry.method} ${shape(entry.path)}`));
  const missing = routes.filter((route) => {
    const key = `${route.method} ${shape(route.path)}`;
    return !shapes.has(shape(route.path)) && !allowed.has(key);
  });
  assert.deepEqual(
    missing.map((route) => `${route.method} ${route.path}`),
    [],
    "这些路由既没有前端消费者、也没有登记在 docs/frontend/UNCONSUMED.md",
  );
});
