/**
 * 真实 API live 链（PLAN-20260915-058 WP-D）：工作区快照文件树与文件级 diff 经真实 HTTP。
 *
 * 后端 = tests/api/console_api_app（Fake Ports，无真实凭据/付费 LLM）：该装配在启动时
 * 建临时快照根、写入两个内容寻址快照，并用一个受控 run 的 evidence 记录两侧 digest
 * （见 console_api_app._with_snapshots）。由 playwrightLive.config.ts 驱动
 * （vite /api 代理 → uvicorn:8011）。
 */

import { expect, test } from "@playwright/test";

const RUN_ID = "11111111-1111-4111-8111-111111111111";
const GHOST_DIGEST = "sha256:" + "c".repeat(64);

interface SnapshotRow {
  digest: string;
  recorded_as: string[];
  retained: boolean;
}

test("live: 能力面报告已配置并给出保留快照数", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });

  const response = await page.request.get("/api/workspace-snapshots");
  expect(response.ok()).toBeTruthy();
  const body = (await response.json()) as { configured: boolean; retained_snapshots: number };
  expect(body.configured).toBe(true);
  expect(body.retained_snapshots).toBe(2);
});

test("live: run 记录的 digest 可解析成文件树（内容寻址）", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });

  const recorded = await page.request.get(`/api/runs/${RUN_ID}/workspace-snapshots`);
  expect(recorded.ok()).toBeTruthy();
  const run = (await recorded.json()) as { snapshots: SnapshotRow[]; note: string };
  expect(run.snapshots).toHaveLength(2);
  expect(run.snapshots.every((row) => row.retained)).toBe(true);
  expect(run.note).toContain("run-to-workspace binding");
  const before = run.snapshots.find((row) => row.recorded_as.includes("EVIDENCE_BEFORE"));
  expect(before).toBeDefined();

  const files = await page.request.get(
    `/api/workspace-snapshots/${encodeURIComponent(before?.digest ?? "")}/files`,
  );
  expect(files.ok()).toBeTruthy();
  const tree = (await files.json()) as {
    digest: string;
    file_count: number;
    total_bytes: number;
    truncated: boolean;
    files: { path: string; size_bytes: number; sha256: string }[];
  };
  expect(tree.digest).toBe(before?.digest);
  expect(tree.truncated).toBe(false);
  expect(tree.files.map((item) => item.path)).toEqual(["notes.md", "src/main.py"]);
  expect(tree.total_bytes).toBe(tree.files.reduce((sum, item) => sum + item.size_bytes, 0));
});

test("live: 两个快照的文件级 diff 报告新增/变化/未变", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });

  const run = (await (
    await page.request.get(`/api/runs/${RUN_ID}/workspace-snapshots`)
  ).json()) as { snapshots: SnapshotRow[] };
  const before = run.snapshots.find((row) => row.recorded_as.includes("EVIDENCE_BEFORE"));
  const after = run.snapshots.find((row) => row.recorded_as.includes("EVIDENCE_AFTER"));
  expect(before && after).toBeTruthy();

  const path = `/api/workspace-snapshots/${encodeURIComponent(before?.digest ?? "")}`;
  const response = await page.request.get(
    `${path}/diff/${encodeURIComponent(after?.digest ?? "")}`,
  );
  expect(response.ok()).toBeTruthy();
  const body = (await response.json()) as {
    comparison: string;
    identical: boolean;
    added: number;
    removed: number;
    changed: number;
    unchanged: number;
    changes: { path: string; kind: string }[];
    note: string;
  };
  expect(body.comparison).toBe("WORKSPACE_SNAPSHOT_METADATA");
  expect(body.identical).toBe(false);
  expect([body.added, body.removed, body.changed, body.unchanged]).toEqual([1, 0, 1, 1]);
  expect(body.changes.map((item) => `${item.kind}:${item.path}`).sort()).toEqual([
    "ADDED:src/util.py",
    "CHANGED:src/main.py",
  ]);
  expect(body.note).toContain("file-level comparison only");
});

test("live: 未保留 digest 与未知 run 都如实 404", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });

  const ghost = await page.request.get(
    `/api/workspace-snapshots/${encodeURIComponent(GHOST_DIGEST)}/files`,
  );
  expect(ghost.status()).toBe(404);
  const problem = (await ghost.json()) as { title: string };
  expect(problem.title).toBe("Snapshot Not Retained");

  const unknownRun = await page.request.get(
    "/api/runs/22222222-2222-4222-8222-222222222222/workspace-snapshots",
  );
  expect(unknownRun.status()).toBe(404);
});
