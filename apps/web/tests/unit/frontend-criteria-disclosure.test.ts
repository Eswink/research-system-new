/**
 * GOAL-20260923-013 EC-03 判据：**判据性质披露必须完备、字段非空、且与实际敏感面一致**。
 *
 * 四条判据（离线、零出网、只读文件事实）：
 * ① **完备性（双向）**——本 GOAL 新增的每个判据文件里解析出的每条 test 都在登记册里，
 *    且登记册不许多出条目（既查漏，也查幽灵行）；
 * ② **两字段非空**——每条登记的「能被什么按压」与「不能被什么按压」都非空、且不是
 *    「判据绿」这类空话（EC-03 明文禁止只写「判据绿」）；
 * ③ **披露与证据一致**——披露 `sensitiveFace: "page"` 的条目必须引用 `press`/`spotcheck`
 *    类红证；披露 `"structure"` 的条目同样必须引用证据；
 * ④ **文档视图同源**——`docs/frontend/CONSOLE_FRONTEND_CRITERIA_DISCLOSURE.md` 里的
 *    每条 test 名都必须在登记册里存在（防两份手工表各漂）。
 *
 * 本测试**不**重跑按压（那是 live/人工步骤），它强制的是「披露在册且与已落证据对得上」；
 * 抽查实跑证明披露为真由 `RECHECK-20260923-154` 承担（成对红/绿落 `scratch/`）。
 */

import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

import { CRITERIA_DISCLOSURE, CRITERIA_SPECS } from "./frontend-criteria-disclosure";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const WEB_ROOT = path.join(HERE, "../..");
const REPO_ROOT = path.join(WEB_ROOT, "../..");
const DOC_PATH = path.join(REPO_ROOT, "docs/frontend/CONSOLE_FRONTEND_CRITERIA_DISCLOSURE.md");

/** 从 spec 源码里解析 test 名（与本仓既有写法一致：`test("…", …)` 起一行）。 */
function testTitles(relativeSpec: string): string[] {
  const source = readFileSync(path.join(WEB_ROOT, relativeSpec), "utf8");
  return [...source.matchAll(/\n(?:test|it)\(\s*"([^"]+)"/g)].map((match) => match[1] ?? "");
}

function registeredTitles(relativeSpec: string): string[] {
  return CRITERIA_DISCLOSURE.filter((row) => row.spec === relativeSpec).map((row) => row.testTitle);
}

/** EC-03 禁止的空话：只写「判据绿」不算披露。 */
const EMPTY_WORDS = ["判据绿", "无", "-", "N/A"];

test("① 披露完备性：每个新增判据文件里的每条 test 都在册，且不许多出", () => {
  for (const spec of CRITERIA_SPECS) {
    assert.ok(existsSync(path.join(WEB_ROOT, spec)), `判据文件不存在: ${spec}`);
    const found = testTitles(spec).sort();
    const registered = registeredTitles(spec).sort();
    assert.ok(found.length > 0, `未从 ${spec} 解析出任何 test`);
    assert.deepEqual(
      registered,
      found,
      `${spec} 的登记册与实际 test 不一致（缺登记或多幽灵行）`,
    );
  }
  const specsInRegister = new Set(CRITERIA_DISCLOSURE.map((row) => row.spec));
  assert.deepEqual(
    [...specsInRegister].sort(),
    [...CRITERIA_SPECS].sort(),
    "登记册覆盖的 spec 集合与 D-1 的枚举口径不一致",
  );
});

test("② 每条的「能被什么按压 / 不能被什么按压」都非空且不是空话", () => {
  for (const row of CRITERIA_DISCLOSURE) {
    const label = `${row.spec} › ${row.testTitle}`;
    for (const [field, value] of [
      ["pressTarget", row.pressTarget],
      ["insensitiveFace", row.insensitiveFace],
    ] as const) {
      assert.ok(value.trim().length > 0, `${label} 的 ${field} 为空`);
      assert.ok(
        !EMPTY_WORDS.includes(value.trim()),
        `${label} 的 ${field} 是空话（EC-03 禁止只写「判据绿」）`,
      );
    }
  }
});

test("③ 披露的敏感面与所引证据类型一致（按页面披露必须有按压证据）", () => {
  for (const row of CRITERIA_DISCLOSURE) {
    const label = `${row.spec} › ${row.testTitle}`;
    assert.ok(row.evidence.length > 0, `${label} 未引用任何按压证据`);
    const pressLike = row.evidence.filter(
      (item) => item.includes("press") || item.includes("spotcheck"),
    );
    assert.ok(pressLike.length > 0, `${label} 的证据里没有按压类红证: ${row.evidence.join(", ")}`);
    if (row.sensitiveFace === "page") {
      assert.ok(
        row.insensitiveFace.includes("数据"),
        `${label} 披露为按页面敏感时必须点名「数据不敏感」那一面`,
      );
      assert.ok(row.premiseIsDataSensitive, `${label} 披露按页面敏感时前提应为数据敏感`);
    } else {
      assert.ok(
        row.insensitiveFace.includes("断言强度"),
        `${label} 披露为结构判据时必须点名「改断言强度不敏感」这一面`,
      );
      assert.ok(!row.premiseIsDataSensitive, `${label} 结构判据不应声明前提数据敏感`);
    }
  }
});

test("④ 文档视图与登记册同源（每条 test 名都在文档里出现）", () => {
  assert.ok(existsSync(DOC_PATH), `披露文档不存在: ${DOC_PATH}`);
  const doc = readFileSync(DOC_PATH, "utf8");
  for (const row of CRITERIA_DISCLOSURE) {
    assert.ok(
      doc.includes(row.testTitle),
      `披露文档缺少登记册里的这条 test: ${row.spec} › ${row.testTitle}`,
    );
  }
});
