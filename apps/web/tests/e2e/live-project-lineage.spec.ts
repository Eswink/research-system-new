/**
 * 真实 FastAPI HTTP + 浏览器集成（PLAN-20260915-055 WP-B / G9 项目级血缘）。
 *
 * 后端为 tests/api/console_api_app（Fake Ports，无真实凭据/付费 LLM）。验证
 * `GET /projects/{id}/lineage` 在真实装配面上：合并图结构、库资源未连边清单、
 * reference_recording 诚实标注，以及未知项目 404（不伪装空成功）。
 */

import { expect, test } from "@playwright/test";

function idem(prefix: string): Record<string, string> {
  return { "Idempotency-Key": `${prefix}-${String(Date.now())}` };
}

test("live: 项目级血缘合并图 + 未连边库资源", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });

  const created = await page.request.post("/api/projects/example-project/library", {
    headers: idem("live-g9-lib"),
    data: { kind: "dataset", name: "g9 live dataset", description: "d", tags: ["g9"] },
  });
  expect(created.status()).toBe(201);

  const response = await page.request.get("/api/projects/example-project/lineage");
  expect(response.ok()).toBeTruthy();
  const merge = (await response.json()) as {
    project_id: string;
    run_count: number;
    nodes: { id: string; kind: string; run_ids: string[]; shared: boolean }[];
    edges: unknown[];
    library_resources: { id: string; kind: string; name: string }[];
    reference_recording: string;
    reference_recording_reason: string;
    degraded: boolean;
  };
  expect(merge.project_id).toBe("example-project");
  expect(Array.isArray(merge.nodes)).toBe(true);
  expect(Array.isArray(merge.edges)).toBe(true);

  // 引用面没有记录：如实标注，且不凭猜造边（资源只出现在未连边清单）。
  expect(merge.reference_recording).toBe("NOT_RECORDED");
  expect(merge.reference_recording_reason).toContain("无记录面");
  expect(merge.library_resources.map((item) => item.name)).toContain("g9 live dataset");
  expect(merge.library_resources.some((item) => item.kind === "dataset")).toBe(true);

  // 共享节点语义：run_ids 多值 ⇔ shared=true（同一节点被多个 run 贡献）。
  for (const node of merge.nodes) {
    expect(node.shared).toBe(node.run_ids.length > 1);
  }

  // 未知项目与 /projects/{id}/runs 同口径：空图而非 404（不伪装有数据）。
  const ghost = await page.request.get("/api/projects/ghost-project/lineage");
  expect(ghost.status()).toBe(200);
  const empty = (await ghost.json()) as {
    run_count: number;
    nodes: unknown[];
    edges: unknown[];
    library_resources: unknown[];
  };
  expect(empty.run_count).toBe(0);
  expect(empty.nodes).toEqual([]);
  expect(empty.edges).toEqual([]);
  expect(empty.library_resources).toEqual([]);
});
