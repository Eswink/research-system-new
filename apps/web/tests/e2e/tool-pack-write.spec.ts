/**
 * Console e2e（PLAN-20260915-065 EC-02）：ToolPack 供应链写面。
 *
 * 核心口径（AC-03）：**待批准 ≠ 已生效**。扩张更新提交后横幅出现、
 * 表里的生效 digest 不变；批准后横幅消失、digest 才变成候选值。
 * 另验证 digest 重算（422 detail 落在面板内）与吊销理由必填 / 终态。
 */

import { expect, test, type Page } from "@playwright/test";

import { assertNoUnmatched, stubApi } from "./stub-api";
import { resetToolPackStub, stubManifestDocument } from "./stub-routes-toolpacks";

const PACK_ID = "console_pack";
const BASE = stubManifestDocument({ id: PACK_ID, capabilities: ["dataset.read"] });
const EXPANDED = stubManifestDocument({
  id: PACK_ID,
  version: "1.1.0",
  capabilities: ["dataset.read", "audit.write"],
});

test.beforeEach(() => {
  resetToolPackStub();
});

test.afterEach(() => {
  assertNoUnmatched();
});

async function openIntegrations(page: Page): Promise<void> {
  await stubApi(page);
  await page.goto("/#/ops/integrations");
  await expect(page.getByTestId("integrations-page")).toBeVisible();
  await expect(page.getByTestId("toolpack-panel")).toBeVisible();
}

async function submitManifest(page: Page, document: Record<string, unknown>): Promise<void> {
  await page.getByTestId("toolpack-manifest-input").fill(JSON.stringify(document));
  await page.getByTestId("toolpack-install-submit").click();
}

async function effectiveDigest(page: Page): Promise<string | null> {
  return page.getByTestId(`toolpack-digest-${PACK_ID}`).getAttribute("title");
}

test("空列表是正确状态：给出说明而不是错误态", async ({ page }) => {
  await openIntegrations(page);
  await expect(page.getByTestId("toolpack-panel")).toContainText("尚未安装任何 ToolPack");
  await expect(page.getByTestId("toolpack-note")).toContainText("REVOKE 为终态");
});

test("安装：digest 由服务端重算校验，pack 出现在表里", async ({ page }) => {
  await openIntegrations(page);
  await submitManifest(page, BASE);

  await expect(page.getByTestId(`toolpack-state-${PACK_ID}`)).toContainText("INSTALLED");
  await expect(page.getByTestId(`toolpack-capabilities-${PACK_ID}`)).toContainText("dataset.read");
  expect(await effectiveDigest(page)).toBe(String(BASE.digest));
  await expect(page.getByTestId("toolpack-install-result")).toContainText("已安装");
});

test("digest 与内容不符：422 detail 在面板内可见，且未写入", async ({ page }) => {
  await openIntegrations(page);
  const tampered = { ...BASE, license: "GPL-3.0" };
  await submitManifest(page, tampered);

  await expect(page.getByTestId("toolpack-install-error")).toContainText("digest mismatch");
  await expect(page.getByTestId(`toolpack-id-${PACK_ID}`)).toHaveCount(0);
});

test("扩张更新登记为待批准：横幅给出 diff，生效 digest 不变", async ({ page }) => {
  await openIntegrations(page);
  await submitManifest(page, BASE);
  expect(await effectiveDigest(page)).toBe(String(BASE.digest));

  await submitManifest(page, EXPANDED);
  await expect(page.getByTestId("toolpack-pending-banner")).toBeVisible();
  await expect(page.getByTestId(`toolpack-diff-${PACK_ID}`)).toContainText("audit.write");
  await expect(page.getByTestId(`toolpack-state-${PACK_ID}`)).toContainText("待批准");
  // 生效版本仍是旧 digest——候选值只在横幅里。
  expect(await effectiveDigest(page)).toBe(String(BASE.digest));
  await expect(page.getByTestId("toolpack-install-result")).toContainText("未生效");
});

test("批准扩张：横幅消失，生效 digest 变为候选值", async ({ page }) => {
  await openIntegrations(page);
  await submitManifest(page, BASE);
  await submitManifest(page, EXPANDED);
  await expect(page.getByTestId(`toolpack-pending-${PACK_ID}`)).toBeVisible();

  await page.getByTestId(`toolpack-approve-${PACK_ID}`).click();
  await expect(page.getByTestId("toolpack-pending-banner")).toHaveCount(0);
  expect(await effectiveDigest(page)).toBe(String(EXPANDED.digest));
  await expect(page.getByTestId(`toolpack-capabilities-${PACK_ID}`)).toContainText("audit.write");
});

test("吊销：理由必填，终态行不再提供处置动作", async ({ page }) => {
  await openIntegrations(page);
  await submitManifest(page, BASE);

  await expect(page.getByTestId(`toolpack-revoke-${PACK_ID}`)).toBeDisabled();
  await page.getByTestId(`toolpack-revoke-reason-${PACK_ID}`).fill("上游来源不可信");
  await page.getByTestId(`toolpack-revoke-${PACK_ID}`).click();

  await expect(page.getByTestId(`toolpack-revoked-${PACK_ID}`)).toContainText("上游来源不可信");
  await expect(page.getByTestId(`toolpack-revoke-${PACK_ID}`)).toHaveCount(0);
  await expect(page.getByTestId(`toolpack-state-${PACK_ID}`)).toContainText("REVOKED");
  expect(await effectiveDigest(page)).toBe(String(BASE.digest));
});
