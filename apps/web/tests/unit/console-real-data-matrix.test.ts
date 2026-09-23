/**
 * GOAL-20260923-013 EC-01 判据：逐页真实数据验收矩阵必须**完备、三方同源、收敛有证**。
 *
 * 三条判据（离线、零出网、只读文件与代码事实）：
 * ① **完备性**——矩阵恰好 20 行，每行终态 ∈ {收敛, 保持}，且无一行含「待定/含糊/待确认」字样；
 * ② **三方同源**——矩阵路由集合 == `pageSupport` 里等级非 `full` 的路由集合；
 *    每条**保持**行的「点名缺口」列必须含一个缺口 token（`API:`/`FIELD:`/`SURFACE:`/`DESIGN:`）
 *    并含一段「」引文，该引文须**逐字**出现在 `pageSupport.ts` 或 `CONSOLE_PAGE_MAP.md` 里
 *    —— 矩阵不得自造缺口事实；
 * ③ **收敛有证**——每条**收敛**行必须含 `LIVE:<spec 文件名>`，该文件须存在，且其 suite 名
 *    须在 `tests/e2e/live-specs.ts` 的白名单内。
 *
 * 另加**互斥**（EC-01 的「不得混写」）：收敛行不得带缺口 token，保持行不得带 `LIVE:`。
 *
 * 本测试只读代码与文档事实，不依赖运行中的后端；页面级 live 证明由 live 套件负责。
 */

import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

import { CANONICAL_ROUTES } from "../../src/navigation/registry";
import { pageSupport } from "../../src/navigation/pageSupport";
import { LIVE_SPEC_PATTERN } from "../e2e/live-specs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const WEB_ROOT = path.join(HERE, "../..");
const REPO_ROOT = path.join(WEB_ROOT, "../..");

const MATRIX_PATH = path.join(REPO_ROOT, "docs/frontend/CONSOLE_REAL_DATA_MATRIX.md");
const SUPPORT_PATH = path.join(WEB_ROOT, "src/navigation/pageSupport.ts");
const PAGE_MAP_PATH = path.join(REPO_ROOT, "docs/frontend/CONSOLE_PAGE_MAP.md");

const GAP_TOKENS = ["API:", "FIELD:", "SURFACE:", "DESIGN:"];
const UNDECIDED = ["待定", "含糊", "待确认", "PENDING"];
const TERMINALS = new Set(["收敛", "保持"]);

/**
 * 取 `LIVE:<spec 文件名>` 的名字部分。
 *
 * 用 `indexOf` + `split` 而不是正则 `String#match`：后者会被 lint 的
 * `prefer-regexp-exec` 拦下（要求改用 `RegExp#exec`，而那又与安全扫描的
 * 命令执行启发式冲突）——这条判据没必要为此引入正则。
 */
function liveSpecName(gap: string): string {
  const at = gap.indexOf("LIVE:");
  if (at < 0) return "";
  return gap.slice(at + "LIVE:".length).split(/[\s；;)]/)[0] ?? "";
}
/** 该 live 用例必须**驱动该路由**并对 DOM 断言，否则「收敛」只是文件存在。 */
const DOM_ASSERTION = /toHaveText|toBeVisible|toContainText/;

/**
 * 路由串是否出现在一次 `page.goto(...)` 调用里。
 *
 * **不能**只 `spec.includes("#/" + route)`：文件头注释里写一句路由就能骗过它
 * （本判据的按压实测暴露过这一点）。这里要求路由串前面 300 字符内出现 `page.goto(`。
 */
function drivesRoute(spec: string, route: string): boolean {
  const needle = `#/${route}`;
  for (let at = spec.indexOf(needle); at >= 0; at = spec.indexOf(needle, at + 1)) {
    if (spec.slice(Math.max(0, at - 300), at).includes("page.goto(")) return true;
  }
  return false;
}

interface Row {
  index: number;
  route: string;
  level: string;
  terminal: string;
  gap: string;
  why: string;
  raw: string;
}

function readOrFail(file: string): string {
  assert.ok(existsSync(file), `missing authority file: ${file}`);
  return readFileSync(file, "utf8");
}

/** 单元格去 markdown 装饰（**粗体** 与 `反引号`），便于逐条比对。 */
function clean(cell: string): string {
  return cell.replace(/\*\*/g, "").replace(/`/g, "").trim();
}

/** 逐行解析「## 逐页矩阵」下的表格；表头与分隔行按位置跳过。 */
function matrixRows(): Row[] {
  const text = readOrFail(MATRIX_PATH);
  const start = text.indexOf("## 逐页矩阵");
  assert.ok(start >= 0, "matrix document must contain the 「## 逐页矩阵」 section");
  return text
    .slice(start)
    .split("\n")
    .filter((line) => line.startsWith("|"))
    .slice(2)
    .map((line) => line.split("|").slice(1, -1).map(clean))
    .filter((cells) => cells.length >= 7 && /^\d+$/.test(cells[0] ?? ""))
    .map((cells) => ({
      index: Number(cells[0]),
      route: cells[1] ?? "",
      level: cells[2] ?? "",
      terminal: cells[3] ?? "",
      gap: cells[5] ?? "",
      why: cells[6] ?? "",
      raw: cells.join(" | "),
    }));
}

/** 三条读面权威的文本：`pageSupport.ts` 的拼接字符串先接回整句再比。 */
function authorityText(): string {
  const support = readOrFail(SUPPORT_PATH).replace(/"\s*\+\s*\n\s*"/g, "");
  return `${support}\n${readOrFail(PAGE_MAP_PATH)}`;
}

function quotes(cell: string): string[] {
  return [...cell.matchAll(/「([^」]+)」/g)].map((match) => match[1] ?? "");
}

/** 规范路由的 key → Route 映射（等级判定与矩阵逐条对应）。 */
const ROUTE_BY_KEY = new Map(
  CANONICAL_ROUTES.map((route) => [`${route.domain}/${route.page}`, route]),
);

function levelOf(route: string): string | null {
  const found = ROUTE_BY_KEY.get(route);
  return found === undefined ? null : pageSupport(found).level;
}

test("① 矩阵完备：恰好 20 行，终态二选一，零条待定", () => {
  const rows = matrixRows();
  assert.equal(rows.length, 20, "matrix must have exactly 20 rows");
  assert.deepEqual(
    rows.map((row) => row.index),
    Array.from({ length: 20 }, (_, i) => i + 1),
    "matrix row numbers must be 1..20 without gaps",
  );
  for (const row of rows) {
    assert.ok(
      TERMINALS.has(row.terminal),
      `row ${String(row.index)} (${row.route}) terminal must be 收敛 or 保持, got ${row.terminal}`,
    );
    for (const word of UNDECIDED) {
      assert.ok(
        !row.raw.includes(word),
        `row ${String(row.index)} (${row.route}) still carries undecided wording ${word}`,
      );
    }
  }
});

test("② 三方同源：非 full 路由无遗漏；收敛行在代码里确为 full；缺口引文逐字来自权威", () => {
  const rows = matrixRows();
  const listed = new Set(rows.map((row) => row.route));
  for (const route of listed) {
    assert.ok(ROUTE_BY_KEY.has(route), `matrix lists a non-canonical route: ${route}`);
  }
  // 非 full 的路由**不得**逃出矩阵；收敛行必须在代码里真的收敛为 full。
  for (const [key] of ROUTE_BY_KEY) {
    if (levelOf(key) === "full") continue;
    assert.ok(listed.has(key), `non-full route missing from the matrix: ${key}`);
  }
  for (const row of rows) {
    if (row.terminal !== "收敛") continue;
    assert.equal(
      levelOf(row.route),
      "full",
      `converged row ${String(row.index)} (${row.route}) is not full in pageSupport`,
    );
  }
  const authority = authorityText();
  for (const row of rows) {
    if (row.terminal !== "保持") continue;
    assert.ok(
      GAP_TOKENS.some((token) => row.gap.includes(token)),
      `held row ${String(row.index)} (${row.route}) must name a gap token`,
    );
    const found = quotes(row.gap).filter((quote) => authority.includes(quote));
    assert.ok(
      found.length > 0,
      `held row ${String(row.index)} (${row.route}) must quote its gap verbatim from ` +
        "pageSupport.ts or CONSOLE_PAGE_MAP.md",
    );
    if (/SURFACE:|DESIGN:/.test(row.gap)) {
      assert.ok(
        row.gap.includes("不做的原因："),
        `held row ${String(row.index)} (${row.route}) uses SURFACE/DESIGN and must say why not now`,
      );
    }
  }
});

test("③ 收敛有证：每条收敛行点名的 live 用例存在、在白名单内、且真的驱动该路由并对 DOM 断言", () => {
  const converged = matrixRows().filter((row) => row.terminal === "收敛");
  assert.ok(converged.length > 0, "at least one row must have converged with live proof");
  for (const row of converged) {
    const file = liveSpecName(row.gap);
    assert.notEqual(
      file,
      "",
      `converged row ${String(row.index)} (${row.route}) must name LIVE:<spec file>`,
    );
    const specPath = path.join(WEB_ROOT, "tests/e2e", file);
    assert.ok(
      existsSync(specPath),
      `converged row ${String(row.index)} names a live spec that does not exist: ${file}`,
    );
    assert.notEqual(
      file.match(LIVE_SPEC_PATTERN),
      null,
      `converged row ${String(row.index)} names a spec outside the live whitelist: ${file}`,
    );
    const spec = readOrFail(specPath);
    assert.ok(
      drivesRoute(spec, row.route),
      `converged row ${String(row.index)} live spec never navigates to ${row.route}: ${file}`,
    );
    assert.ok(
      DOM_ASSERTION.test(spec),
      `converged row ${String(row.index)} live spec asserts nothing on the DOM: ${file}`,
    );
  }
});

test("④ 不混写：收敛行不带缺口 token，保持行不带 LIVE:", () => {
  for (const row of matrixRows()) {
    if (row.terminal === "收敛") {
      for (const token of GAP_TOKENS) {
        assert.ok(
          !row.gap.includes(token),
          `converged row ${String(row.index)} (${row.route}) must not carry gap token ${token}`,
        );
      }
    } else {
      assert.ok(
        !row.gap.includes("LIVE:"),
        `held row ${String(row.index)} (${row.route}) must not carry LIVE: evidence`,
      );
    }
  }
});
