/**
 * 真实 API live 链（PLAN-20260915-065 EC-02 / AC-06）：ToolPack install → 扩张待批准 →
 * 批准 → 吊销，经真实 HTTP 与真实 SQLite store 走一遍。
 *
 * 后端 = tests/api/console_api_app（Fake Ports，无真实凭据/付费 LLM），由
 * playwrightLive.config.ts 驱动（vite /api 代理 → uvicorn:8011）。
 * manifest 由域代码生成（`tests/tooling/test_console_toolpack_fixtures.py` 守同步）：
 * 控制面会重算内容 digest，手写 digest 只会在 422 上打转。
 */

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { expect, test, type Page } from "@playwright/test";

const PACK_ID = "live_console_pack";
const FIXTURE = fileURLToPath(new URL("./fixtures/toolpack-live-manifests.json", import.meta.url));

interface ManifestDocument {
  digest: string;
  [key: string]: unknown;
}

interface LiveFixture {
  base: ManifestDocument;
  expanded: ManifestDocument;
}

const { base, expanded } = JSON.parse(readFileSync(FIXTURE, "utf8")) as LiveFixture;

const idem = (tag: string) => ({ "Idempotency-Key": `live-065-${tag}-${String(Date.now())}` });

interface PackRow {
  id: string;
  state: string;
  digest: string;
  pending: { digest: string } | null;
  catalog_digest_active: boolean;
}

async function packRow(page: Page): Promise<PackRow | undefined> {
  const response = await page.request.get("/api/tool-packs");
  const body = (await response.json()) as { packs: PackRow[] };
  return body.packs.find((item) => item.id === PACK_ID);
}

/** 前置清理：本 id 若是上一轮遗留（REVOKED 终态）会挡住整条链，先退出目录。 */
async function cleanPrevious(page: Page): Promise<void> {
  const existing = await packRow(page);
  if (existing === undefined) return;
  expect(existing.state).toBe("REVOKED");
  await page.request.post(`/api/tool-packs/${PACK_ID}/revoke`, {
    headers: idem("cleanup"),
    data: { reason: "live 前置清理（上一轮遗留）" },
  });
}

function effectiveDigest(page: Page): Promise<string | null> {
  return page.getByTestId(`toolpack-digest-${PACK_ID}`).getAttribute("title");
}

async function submitManifest(page: Page, document: ManifestDocument): Promise<void> {
  await page.getByTestId("toolpack-manifest-input").fill(JSON.stringify(document));
  await page.getByTestId("toolpack-install-submit").click();
}

test("live: install → 扩张待批准 → 批准 → 吊销（读面随写面变化）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await cleanPrevious(page);
  await page.goto("/#/ops/integrations", { waitUntil: "domcontentloaded" });
  await page.reload();
  await expect(page.getByTestId("toolpack-panel")).toBeVisible();

  await submitManifest(page, base);
  await expect(page.getByTestId(`toolpack-state-${PACK_ID}`)).toContainText("INSTALLED");
  expect(await effectiveDigest(page)).toBe(base.digest);
  expect((await packRow(page))?.digest).toBe(base.digest);

  // 扩张：登记为待批准——生效 digest 不变，候选 digest 只在横幅里。
  await submitManifest(page, expanded);
  await expect(page.getByTestId(`toolpack-pending-${PACK_ID}`)).toBeVisible();
  await expect(page.getByTestId(`toolpack-diff-${PACK_ID}`)).toContainText("audit.write");
  expect(await effectiveDigest(page)).toBe(base.digest);
  const pendingRow = await packRow(page);
  expect(pendingRow?.digest).toBe(base.digest);
  expect(pendingRow?.pending?.digest).toBe(expanded.digest);

  await page.getByTestId(`toolpack-approve-${PACK_ID}`).click();
  await expect(page.getByTestId("toolpack-pending-banner")).toHaveCount(0);
  expect(await effectiveDigest(page)).toBe(expanded.digest);
  expect((await packRow(page))?.digest).toBe(expanded.digest);

  await page.getByTestId(`toolpack-revoke-reason-${PACK_ID}`).fill("live 用例结束清理");
  await page.getByTestId(`toolpack-revoke-${PACK_ID}`).click();
  await expect(page.getByTestId(`toolpack-revoked-${PACK_ID}`)).toContainText("live 用例结束清理");
  const revoked = await packRow(page);
  expect(revoked?.state).toBe("REVOKED");
  expect(revoked?.catalog_digest_active).toBe(false);

  // 终态：同 id 再提交 → 409（服务端拒绝，不静默重装）。
  const again = await page.request.post("/api/tool-packs/install", {
    headers: idem("reinstall"),
    data: { manifest: base },
  });
  expect(again.status()).toBe(409);
});

test("live: digest 与内容不符 → 422，detail 落在面板内", async ({ page }) => {
  await page.goto("/#/ops/integrations", { waitUntil: "domcontentloaded" });
  await expect(page.getByTestId("toolpack-panel")).toBeVisible();

  await submitManifest(page, { ...base, license: "Apache-2.0" });
  await expect(page.getByTestId("toolpack-install-error")).toContainText("digest mismatch");
});
