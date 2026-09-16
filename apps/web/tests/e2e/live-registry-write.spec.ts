/**
 * 真实 API live 链（G15 / PLAN-20260915-060 EC-05）：Tool Provider 注册治理经真实 HTTP。
 *
 * 后端 = tests/api/console_api_app（Fake Ports，无真实凭据/付费 LLM）：该装配的 run-ready
 * deps 带同侧 SQLite ToolProviderRegistry（见 tests/api/run_fixtures._run_ready_sqlite_stores）。
 * 由 playwrightLive.config.ts 驱动（vite /api 代理 → uvicorn:8011）。
 */

import { expect, test } from "@playwright/test";

const PIN = `sha256:${"b".repeat(64)}`;
const idem = (tag: string) => ({ "Idempotency-Key": `live-060-${tag}-${String(Date.now())}` });

interface RegistrationRow {
  id: string;
  state: string;
  trust_level: string;
  catalog_active: boolean;
  last_health: string | null;
}

test("live: 注册→批准→吊销全链，目录随之变化", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });

  const created = await page.request.post("/api/tool-provider-registrations", {
    headers: idem("register"),
    data: {
      id: "live_dataset_gateway",
      kind: "REST",
      capabilities: ["dataset.read"],
      pinned_revision: PIN,
      transport: "rest",
      health_check: true,
    },
  });
  expect(created.status()).toBe(201);
  const registration = (await created.json()) as RegistrationRow;
  expect(registration.state).toBe("PENDING");
  expect(registration.catalog_active).toBe(false);

  // PENDING 不进目录（目录只反映 examples 契约 + 已批准注册）。
  const before = await page.request.get("/api/tool-providers");
  const listed = (await before.json()) as { providers: { id: string }[] };
  expect(listed.providers.map((item) => item.id)).not.toContain("live_dataset_gateway");

  const approved = await page.request.post(
    `/api/tool-provider-registrations/live_dataset_gateway/approve`,
    { headers: idem("approve") },
  );
  expect(approved.ok()).toBeTruthy();
  expect(((await approved.json()) as RegistrationRow).catalog_active).toBe(true);

  const after = await page.request.get("/api/tool-providers");
  const approvedCatalog = (await after.json()) as {
    providers: { id: string; trust_level: string }[];
  };
  const entry = approvedCatalog.providers.find((item) => item.id === "live_dataset_gateway");
  expect(entry?.trust_level).toBe("USER_APPROVED");

  // 健康复核写回事实：无实例时诚实 UNKNOWN（不伪装健康）。
  const checked = await page.request.post(
    "/api/tool-provider-registrations/live_dataset_gateway/health-check",
    { headers: idem("health") },
  );
  expect(checked.ok()).toBeTruthy();
  expect(((await checked.json()) as RegistrationRow).last_health).toBe("UNKNOWN");

  const revoked = await page.request.post(
    "/api/tool-provider-registrations/live_dataset_gateway/revoke",
    { headers: idem("revoke"), data: { reason: "live 复核不通过" } },
  );
  expect(revoked.ok()).toBeTruthy();
  const revokedBody = (await revoked.json()) as RegistrationRow;
  expect(revokedBody.state).toBe("REVOKED");
  expect(revokedBody.catalog_active).toBe(false);

  const finalCatalog = await page.request.get("/api/tool-providers");
  const finalListed = (await finalCatalog.json()) as { providers: { id: string }[] };
  expect(finalListed.providers.map((item) => item.id)).not.toContain("live_dataset_gateway");
});

test("live: 声明的必需凭据不在时如实 UNKNOWN（不伪装健康）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });

  const requiredRef = "LIVE_REGISTRY_REQUIRED_TOKEN_074";
  const created = await page.request.post("/api/tool-provider-registrations", {
    headers: idem("cred-register"),
    data: {
      id: "live_credential_bound",
      kind: "REST",
      capabilities: ["dataset.read"],
      pinned_revision: PIN,
      transport: "rest",
      health_check: true,
      credential_ref: requiredRef,
    },
  });
  expect(created.status()).toBe(201);
  const binding = (
    (await created.json()) as {
      credential_binding: { state: string; credential_ref: string | null; present: boolean };
    }
  ).credential_binding;
  expect(binding.state).toBe("ABSENT");
  expect(binding.credential_ref).toBe(requiredRef);

  const checked = await page.request.post(
    "/api/tool-provider-registrations/live_credential_bound/health-check",
    { headers: idem("cred-health") },
  );
  expect(checked.ok()).toBeTruthy();
  const checkedBody = (await checked.json()) as { last_health: string; health_detail: string };
  expect(checkedBody.last_health).toBe("UNKNOWN");
  expect(checkedBody.health_detail).toContain(requiredRef);
});

test("live: 可漂移 pin 与重复登记被拒绝", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });

  const drifting = await page.request.post("/api/tool-provider-registrations", {
    headers: idem("drifting"),
    data: {
      id: "live_drifting_pin",
      kind: "REST",
      capabilities: ["dataset.read"],
      pinned_revision: "v1.2.3",
      transport: "rest",
    },
  });
  expect(drifting.status()).toBe(422);

  const duplicate = await page.request.post("/api/tool-provider-registrations", {
    headers: idem("duplicate"),
    data: {
      id: "live_dataset_gateway",
      kind: "REST",
      capabilities: ["dataset.read"],
      pinned_revision: PIN,
      transport: "rest",
    },
  });
  expect(duplicate.status()).toBe(409);
});
