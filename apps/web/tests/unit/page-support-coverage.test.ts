/**
 * EC-05 守卫（PLAN-20260914-050）：33 条规范路由的能力声明必须**显式且诚实**。
 *
 * 依据 `docs/frontend/CONSOLE_PAGE_MAP.md` 的支持等级定义：
 * - 每条规范路由都要有自己的 pageSupport 条目（禁止落到 `未登记页面` 的隐式 gap）；
 * - 非 full 等级必须给出可读 reason（"未登记/无原因"不得作为沉默降级）；
 * - `ops/matrix` 是唯一允许的 gap 级页面，且它是界面状态说明页（非业务页）。
 *
 * 本测试只读代码事实，不依赖运行中的后端；live 链路由 live e2e 与 API 套件负责。
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

import { CANONICAL_ROUTES } from "../../src/navigation/registry";
import { pageSupport } from "../../src/navigation/pageSupport";
const SRC = path.join(path.dirname(fileURLToPath(import.meta.url)), "../../src");

/** 允许的 gap 级页面（非业务页：界面状态说明，不消费任何后端能力）。 */
const ALLOWED_GAPS = new Set(["ops/matrix"]);

test("every canonical route declares its own support entry (no implicit gap)", () => {
  const source = readFileSync(path.join(SRC, "navigation/pageSupport.ts"), "utf8");
  // 反证：未登记键确实会落到默认 gap——上面两条断言因此不是空断言。
  assert.equal(
    pageSupport({ domain: "ops", page: "overview" }).reason,
    "未登记页面",
    "default for unregistered keys changed: the coverage assertions would go vacuously true",
  );
  for (const route of CANONICAL_ROUTES) {
    const key = `${route.domain}/${route.page}`;
    assert.match(
      source,
      new RegExp(`"${key.replace(/[/]/g, "\\/")}":`),
      `pageSupport missing explicit entry for ${key}`,
    );
    assert.notEqual(
      pageSupport(route).reason,
      "未登记页面",
      `${key} fell through to the unregistered-page default`,
    );
  }
});

test("non-full levels always carry a readable reason", () => {
  for (const route of CANONICAL_ROUTES) {
    const support = pageSupport(route);
    const key = `${route.domain}/${route.page}`;
    if (support.level === "full") continue;
    assert.ok(
      (support.reason ?? "").trim().length > 0,
      `${key} is ${support.level} without a reason (silent degradation)`,
    );
  }
});

test("gap level is limited to the non-business state-reference page", () => {
  const gaps = CANONICAL_ROUTES.filter((route) => pageSupport(route).level === "gap").map(
    (route) => `${route.domain}/${route.page}`,
  );
  assert.deepEqual(gaps, [...ALLOWED_GAPS]);
});
