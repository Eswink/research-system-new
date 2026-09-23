/**
 * EC-04（GOAL-20260923-013）一致性判据：`ops/matrix` 的「界面状态说明页（非实时运维状态）」
 * 必须是**四处同源**的一等事实，且「为什么不做实时运维状态」要落在文档里、并且**可核对**
 * （点名真实存在、等级如实标注的 live 运维页，而不是一句「设计如此」）。
 *
 * 四处：① `pageSupport.ts` 的 `reason`（逐字不改，只判包含关系）
 * ② `CONSOLE_PAGE_MAP.md` 的 `#/ops/matrix` 小节 ③ 矩阵文档第 15 行
 * ④ **页面可见文案**（i18n 的 `matrix.hint`，由 `GapLayout` 渲染在详情栏）。
 *
 * 判据性质披露（EC-03 口径）：本判据是**文档/源码文本**判据 —— 按压对象是这四处的**措辞**
 * （删短语、把「不做」写成「要做」即红）；**不敏感面**是运行时渲染是否正确
 * （那是 `apps/web/tests/e2e/matrix-states.spec.ts` 的页面判据负责）。
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.join(HERE, "../../../..");

const NATURE = "界面状态说明";
const CONCEPT = "实时运维状态";
/** 「不做实时运维状态」的合法说法（四处至少要出现其中之一）。 */
const NEGATIONS = ["非实时运维状态", "不冒充实时运维状态", "不是实时运维状态", "不做实时运维状态"];

/** 可被点名的运维页候选（真写进文档的必须**存在**，且其中≥1 个等级为 full）。 */
const LIVE_OPS_CANDIDATES = ["ops/data-health", "ops/observability", "ops/compute"];

function readRepo(relative: string): string {
  return readFileSync(path.join(REPO_ROOT, relative), "utf8");
}

/** 取 `anchor`（必要时再右移到 `field`）之后、`:` 之后的第一个引号字符串。 */
function quotedAfter(source: string, anchor: string, field?: string): string {
  const at = source.indexOf(anchor);
  if (at < 0) return "";
  const base = field === undefined ? at : source.indexOf(field, at);
  if (base < 0) return "";
  const colon = source.indexOf(":", base);
  if (colon < 0) return "";
  const open = source.indexOf('"', colon);
  if (open < 0) return "";
  const close = source.indexOf('"', open + 1);
  return close < 0 ? "" : source.slice(open + 1, close);
}

function pageMapSection(source: string): string {
  const marker = "### `#/ops/matrix`";
  const start = source.indexOf(marker);
  if (start < 0) return "";
  const rest = source.slice(start + marker.length);
  const next = rest.indexOf("\n### ");
  return next < 0 ? rest : rest.slice(0, next);
}

function matrixRow(source: string): string {
  return source.split("\n").find((line) => line.startsWith("| 15 | `ops/matrix`")) ?? "";
}

/** `pageSupport.ts` 的路由 → 等级（只取本文关心的 `ops/*`）。 */
function opsLevels(source: string): Map<string, string> {
  const levels = new Map<string, string>();
  const pattern = /"(ops\/[a-z-]+)":\s*\{[^}]*?level:\s*"([a-z]+)"/g;
  for (const found of source.matchAll(pattern)) {
    const route = found[1];
    const level = found[2];
    if (route !== undefined && level !== undefined) {
      levels.set(route, level);
    }
  }
  return levels;
}

function sources(): { label: string; text: string }[] {
  const support = readRepo("apps/web/src/navigation/pageSupport.ts");
  const hint = quotedAfter(readRepo("apps/web/src/i18n/zh.ts"), '"matrix.hint":');
  return [
    { label: "pageSupport.reason", text: quotedAfter(support, '"ops/matrix":', "reason:") },
    {
      label: "CONSOLE_PAGE_MAP 小节",
      text: pageMapSection(readRepo("docs/frontend/CONSOLE_PAGE_MAP.md")),
    },
    { label: "矩阵第 15 行", text: matrixRow(readRepo("docs/frontend/CONSOLE_REAL_DATA_MATRIX.md")) },
    { label: "页面可见文案 matrix.hint", text: hint },
  ];
}

test("① 四处同源：都含「界面状态说明」，且都以否定说法交代「实时运维状态」", () => {
  for (const { label, text } of sources()) {
    assert.ok(text.length > 0, `来源为空: ${label}`);
    assert.ok(text.includes(NATURE), `${label} 缺「${NATURE}」`);
    assert.ok(
      NEGATIONS.some((phrase) => text.includes(phrase)),
      `${label} 缺否定说法（${NEGATIONS.join(" / ")}）`,
    );
  }
});

test("② 四处都提到「实时运维状态」这个概念（不回避口径）", () => {
  for (const { label, text } of sources()) {
    assert.ok(text.includes(CONCEPT), `${label} 未提及「${CONCEPT}」`);
  }
});

test("③ 「为什么不做」点名真实存在的运维页，且等级如实（至少一个 full）", () => {
  const levels = opsLevels(readRepo("apps/web/src/navigation/pageSupport.ts"));
  const all = sources();
  for (const label of ["CONSOLE_PAGE_MAP 小节", "矩阵第 15 行"]) {
    const text = all.find((item) => item.label === label)?.text ?? "";
    const named = LIVE_OPS_CANDIDATES.filter((route) => text.includes(route));
    assert.ok(named.length >= 2, `${label} 未点名 ≥2 个运维页（点名: ${named.join(", ")}）`);
    for (const route of named) {
      assert.ok(levels.has(route), `${label} 点名了不存在的路由 ${route}`);
    }
    assert.ok(
      named.some((route) => levels.get(route) === "full"),
      `${label} 点名的运维页里没有 full 等级的（点名: ${named.join(", ")}）`,
    );
    assert.ok(text.includes("FULL"), `${label} 未标注点名页面的等级`);
  }
});

test("④ 页面接线见证：说明面读的就是这两处文案（渲染由 e2e 判据负责）", () => {
  const page = readRepo("apps/web/src/features/state-reference/StateReferencePage.tsx");
  assert.ok(page.includes('pageSupport({ domain: "ops", page: "matrix" })'), "未消费 support");
  assert.ok(page.includes('t("matrix.hint")'), "未把页面文案接进详情栏");
});
