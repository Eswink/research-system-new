/**
 * 执行体披露读面（`RunDetailDto.execution`）在运行页的接线
 * （GOAL-007 cycle 4 = EC-04）。
 *
 * 判据（与 GOAL 的 EC-04 判定细则对齐）：**读面字段 + 页面渲染分支**——
 * 两种执行体在页面上必须**可区分**，不是"只在 `types.ts` 里存在字段"。四条受控 fixture
 * 覆盖四态：真实执行体 / 受控 demo 执行体 / 已冻结但未声明 / 未冻结（`execution === null`）。
 *
 * 文案边界：`NOT_VERIFIED` 是**状态**不是**指纹值**——页面必须把原因一并显示，
 * 不得把它渲染成指纹结论。
 */

import { expect, test } from "@playwright/test";

import { assertNoUnmatched, stubApi } from "./stub-api";

const CASES = [
  {
    id: "substrate-openhands",
    backend: "openhands",
    fingerprint: "NOT_VERIFIED",
    reason: "no model probe fact was collected",
  },
  {
    id: "substrate-fake",
    backend: "fake",
    fingerprint: "NOT_VERIFIED",
    reason: "the controlled demo runtime makes no model call",
  },
  { id: "rebuild-refused", backend: "未冻结", fingerprint: "未声明", reason: null },
  { id: "substrate-undeclared", backend: "未声明", fingerprint: "未声明", reason: null },
] as const;

test.beforeEach(async ({ page }) => {
  await stubApi(page);
});

test.afterEach(() => {
  assertNoUnmatched();
});

test("两种执行体在页面上可区分，「未声明」与「未冻结」也分开说", async ({ page }) => {
  const seen: string[] = [];
  for (const item of CASES) {
    await page.goto(`/#/run/timeline?run=${item.id}`);
    const backend = page.getByTestId("run-execution-backend");
    await expect(backend).toHaveText(item.backend);
    seen.push((await backend.textContent()) ?? "");
    const fingerprint = page.getByTestId("run-runtime-fingerprint");
    await expect(fingerprint).toContainText(item.fingerprint);
    if (item.reason !== null) {
      await expect(fingerprint).toContainText(item.reason);
    }
  }
  // 三态互不相同（页面不是把同一个值渲染三遍）。
  expect(new Set(seen).size).toBe(CASES.length);
});

test("指纹只报状态：NOT_VERIFIED 连同原因一起显示，不冒充指纹值", async ({ page }) => {
  await page.goto("/#/run/timeline?run=substrate-openhands");
  const fingerprint = page.getByTestId("run-runtime-fingerprint");
  await expect(fingerprint).toContainText("NOT_VERIFIED");
  await expect(fingerprint).toContainText("no model probe fact");
  // 未验证就是未验证：整串必须以 NOT_VERIFIED 开头（不能出现「已验证」的结论）。
  // 注意不能用 `not.toContainText("VERIFIED ·")`——那是 "NOT_VERIFIED ·" 的子串。
  await expect(fingerprint).toHaveText(/^NOT_VERIFIED · /);
  await expect(page.getByTestId("run-execution-backend")).toHaveText("openhands");
});
