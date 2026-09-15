/**
 * 项目注册表真实链路（PLAN-20260915-061 EC-06；自 live-api-workflow 拆出以守
 * 450 行文件上限）。
 *
 * 覆盖：默认条目/创建（自动默认设置行）/草稿按项目归属/归档，以及删除语义
 * ——默认项目与仍被引用的项目 409（不级联研究数据），无引用项目 204 且再见即
 * 404。前端经 vite dev（/api 代理到 8011）加载，后端为 tests/api/console_api_app
 * （Fake Ports：无真实凭据/付费 LLM）。
 */

import { expect, test } from "@playwright/test";

const VALID_DRAFT = [
  "id: live_research_v1_0_0",
  "version: 1.0.0",
  "phases:",
  "  - id: execution",
  "    strategy: single_agent",
  "    required_roles:",
  "      - {role: experiment_engineer, min_instances: 1, max_instances: 1}",
  "    task_contract: live_execution",
  "    timeout_seconds: 120",
].join("\n");

function idem(prefix: string): Record<string, string> {
  return { "Idempotency-Key": `${prefix}-${String(Date.now())}-${String(Math.random())}` };
}

test("live: 项目注册表与归属（WP-C cycle 1）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const defaultList = (await (await page.request.get("/api/projects")).json()) as {
    id: string;
    name: string;
    status: string;
  }[];
  const primary = defaultList.find((item) => item.id === "example-project");
  expect(primary?.id).toBe("example-project");
  expect(primary?.name).toBe("Example ML Research");

  const created = await page.request.post("/api/projects", {
    headers: idem("live-project"),
    data: { name: "Live Registry Study" },
  });
  expect(created.status()).toBe(201);
  const projectId = ((await created.json()) as { id: string }).id;
  const listed = (await (await page.request.get("/api/projects")).json()) as { id: string }[];
  expect(listed.map((item) => item.id)).toContain(projectId);

  // 新注册项目自动带默认设置行（可编辑，不伪装未配置）。
  const settings = await page.request.get(`/api/projects/${projectId}/settings`);
  expect(settings.ok()).toBeTruthy();
  expect(((await settings.json()) as Record<string, unknown>).project_id).toBe(projectId);

  // 草稿按项目归属：新项目可见、其它项目不可见。
  const draft = await page.request.post(`/api/projects/${projectId}/protocol-drafts`, {
    headers: idem("live-project-draft"),
    data: { name: "scoped draft", yaml_text: VALID_DRAFT },
  });
  expect(draft.status()).toBe(201);
  const scoped = (await (
    await page.request.get(`/api/projects/${projectId}/protocol-drafts`)
  ).json()) as unknown[];
  expect(scoped.length).toBe(1);
  const other = (await (
    await page.request.get("/api/projects/example-project/protocol-drafts")
  ).json()) as { draft_id: string }[];
  expect(other.map((item) => item.draft_id)).not.toContain(
    ((await draft.json()) as { draft_id: string }).draft_id,
  );

  // 归档语义；幽灵项目仍 404。
  const archived = await page.request.patch(`/api/projects/${projectId}`, {
    headers: idem("live-project-archive"),
    data: { status: "ARCHIVED" },
  });
  expect(((await archived.json()) as { status: string }).status).toBe("ARCHIVED");
  expect((await page.request.get("/api/projects/ghost-project/settings")).status()).toBe(404);
});

test("live: 项目删除语义（EC-06：引用即 409，无引用才 204）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });

  // 默认项目由 examples 契约合成：拒绝删除（删了也还在，属静默 no-op 陷阱）。
  const reserved = await page.request.delete("/api/projects/example-project", {
    headers: idem("live-project-delete-default"),
  });
  expect(reserved.status()).toBe(409);
  expect(((await reserved.json()) as { title: string }).title).toBe("Project Reserved");

  // 有研究数据引用（草稿）：409 且列出引用清单，数据不被级联删除。
  const created = await page.request.post("/api/projects", {
    headers: idem("live-project-delete"),
    data: { name: "Live Delete Study" },
  });
  expect(created.status()).toBe(201);
  const projectId = ((await created.json()) as { id: string }).id;
  const draft = await page.request.post(`/api/projects/${projectId}/protocol-drafts`, {
    headers: idem("live-project-delete-draft"),
    data: { name: "blocking draft", yaml_text: VALID_DRAFT },
  });
  expect(draft.status()).toBe(201);
  const inUse = await page.request.delete(`/api/projects/${projectId}`, {
    headers: idem("live-project-delete-in-use"),
  });
  expect(inUse.status()).toBe(409);
  expect(((await inUse.json()) as { detail: string }).detail).toContain("drafts=1");
  expect((await page.request.get(`/api/projects/${projectId}/settings`)).ok()).toBeTruthy();

  // 无引用项目：204，注册行与设置行一起消失，再删为 404（不假装成功）。
  const empty = await page.request.post("/api/projects", {
    headers: idem("live-project-delete-empty"),
    data: { name: "Live Delete Empty" },
  });
  const emptyId = ((await empty.json()) as { id: string }).id;
  const removed = await page.request.delete(`/api/projects/${emptyId}`, {
    headers: idem("live-project-delete-empty-row"),
  });
  expect(removed.status()).toBe(204);
  expect((await page.request.get(`/api/projects/${emptyId}/settings`)).status()).toBe(404);
  const again = await page.request.delete(`/api/projects/${emptyId}`, {
    headers: idem("live-project-delete-again"),
  });
  expect(again.status()).toBe(404);
});
