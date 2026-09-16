/**
 * Console e2e（G15 / PLAN-20260915-060 EC-05）：Tool Provider 注册治理写面。
 *
 * 验证"写了之后目录真的变了"：登记后目录不变（PENDING 不入目录），
 * 批准后 provider 以 USER_APPROVED 出现在目录里，吊销后退出目录；
 * 吊销理由必填，终态行不再提供处置动作。
 */

import { expect, test, type Page } from "@playwright/test";

import { assertNoUnmatched, stubApi } from "./stub-api";
import { resetRegistryStub, scriptSchemaDrift, scriptSchemaStable } from "./stub-routes-registry";

const PIN = `sha256:${"a".repeat(64)}`;

test.beforeEach(() => {
  resetRegistryStub();
});

test.afterEach(() => {
  assertNoUnmatched();
});

async function openIntegrations(page: Page): Promise<void> {
  await stubApi(page);
  await page.goto("/#/ops/integrations");
  await expect(page.getByTestId("integrations-page")).toBeVisible();
  await expect(page.getByTestId("registry-panel")).toBeVisible();
}

async function registerProvider(page: Page, providerId: string): Promise<void> {
  await page.getByTestId("registry-id").fill(providerId);
  await page.getByTestId("registry-capabilities").fill("dataset.read");
  await page.getByTestId("registry-pin").fill(PIN);
  await page.getByTestId("registry-submit").click();
}

test("登记后为 PENDING：目录不变，注册表可见", async ({ page }) => {
  await openIntegrations(page);
  await registerProvider(page, "dataset_gateway");

  await expect(page.getByTestId("registry-state-PENDING")).toContainText("UNTRUSTED");
  const catalog = page.getByRole("table", { name: "Tool Provider 目录", exact: true });
  await expect(catalog).not.toContainText("dataset_gateway");
});

test("批准后 provider 进入目录（USER_APPROVED）", async ({ page }) => {
  await openIntegrations(page);
  await registerProvider(page, "dataset_gateway");
  await page.getByTestId("registry-approve").click();

  await expect(page.getByTestId("registry-state-ACTIVE")).toContainText("USER_APPROVED");
  const catalog = page.getByRole("table", { name: "Tool Provider 目录", exact: true });
  await expect(catalog).toContainText("dataset_gateway");
  await expect(catalog).toContainText("USER_APPROVED");
});

test("吊销后退出目录，且终态行不再有处置动作", async ({ page }) => {
  await openIntegrations(page);
  await registerProvider(page, "dataset_gateway");
  await page.getByTestId("registry-approve").click();
  await expect(page.getByTestId("registry-actions")).toBeVisible();

  await page.getByTestId("registry-revoke-reason").fill("上游被替换");
  await page.getByTestId("registry-revoke").click();
  await expect(page.getByTestId("registry-revoked")).toContainText("上游被替换");
  await expect(page.getByTestId("registry-actions")).toHaveCount(0);
  const catalog = page.getByRole("table", { name: "Tool Provider 目录", exact: true });
  await expect(catalog).not.toContainText("dataset_gateway");
});

test("吊销理由为空时按钮禁用（理由必须留痕）", async ({ page }) => {
  await openIntegrations(page);
  await registerProvider(page, "dataset_gateway");
  await expect(page.getByTestId("registry-revoke")).toBeDisabled();
});

test("健康复核写入事实并在注册表行显示", async ({ page }) => {
  await openIntegrations(page);
  await registerProvider(page, "dataset_gateway");
  await page.getByTestId("registry-health-check").click();
  await expect(page.getByTestId("registry-health-dataset_gateway")).toContainText("UNKNOWN");
});

// --- schema 漂移可见（PLAN-20260915-069 / EC-02 剩余子句）----------------------------------

const DIGEST_A = `sha256:${"1".repeat(64)}`;
const DIGEST_B = `sha256:${"2".repeat(64)}`;

test("schema 漂移在注册表行上可见，并给出可比对的两个指纹", async ({ page }) => {
  scriptSchemaDrift(DIGEST_A, DIGEST_B);
  await openIntegrations(page);
  await registerProvider(page, "dataset_gateway");
  await page.getByTestId("registry-health-check").click();

  const marker = page.getByTestId("registry-schema-drift-dataset_gateway");
  await expect(marker).toBeVisible();
  await expect(marker).toContainText("schema 漂移");
  // 可比对：漂移前后各截 12 位 hex（完整值仍在 DTO 里，行内只做肉眼区分）
  await expect(marker).toContainText("111111111111");
  await expect(marker).toContainText("222222222222");
});

test("无漂移时不出现漂移标记（对照组：不是恒显示的装饰）", async ({ page }) => {
  scriptSchemaStable(DIGEST_A);
  await openIntegrations(page);
  await registerProvider(page, "dataset_gateway");
  await page.getByTestId("registry-health-check").click();

  await expect(page.getByTestId("registry-health-dataset_gateway")).toContainText("HEALTHY");
  await expect(page.getByTestId("registry-schema-drift-dataset_gateway")).toHaveCount(0);
});
