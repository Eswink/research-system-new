/**
 * Console e2e（PLAN-20260915-058 WP-D）：工作区快照文件树与文件级 Diff。
 *
 * 确定性 API 替身 + 用例内覆盖（不改动全局 stub fixture，避免搅动 design-fidelity
 * 基线）：验证 run 记录的快照与保留状态、单快照文件树、两快照文件级差异，
 * 以及"未保留/未配置"时不渲染假树。
 */

import { expect, test, type Page } from "@playwright/test";

import { assertNoUnmatched, stubApi } from "./stub-api";

const RUN_ID = "run-stub-snapshots";
const DIGEST_A = "sha256:" + "a".repeat(64);
const DIGEST_B = "sha256:" + "b".repeat(64);

const EXPERIMENTS = {
  experiments: [],
  reproduction_note: "stub fixture: reproduction needs the original environment digest",
};

const RECORDED = {
  run_id: RUN_ID,
  snapshots: [
    { digest: DIGEST_A, recorded_as: ["EVIDENCE_BEFORE"], retained: true },
    { digest: DIGEST_B, recorded_as: ["EVIDENCE_AFTER"], retained: true },
  ],
  note: "these are the snapshot digests this run recorded (evidence/experiment)",
};

const TREE_A = {
  digest: DIGEST_A,
  files: [
    { path: "notes.md", size_bytes: 12, sha256: "1".repeat(64) },
    { path: "src/main.py", size_bytes: 340, sha256: "2".repeat(64) },
  ],
  file_count: 2,
  total_bytes: 352,
  truncated: false,
};

const DIFF = {
  left_digest: DIGEST_A,
  right_digest: DIGEST_B,
  comparison: "WORKSPACE_SNAPSHOT_METADATA",
  identical: false,
  added: 1,
  removed: 0,
  changed: 1,
  unchanged: 1,
  changes: [
    {
      path: "src/main.py",
      kind: "CHANGED",
      left_sha256: "2".repeat(64),
      right_sha256: "3".repeat(64),
      left_size_bytes: 340,
      right_size_bytes: 352,
    },
    {
      path: "src/util.py",
      kind: "ADDED",
      left_sha256: null,
      right_sha256: "4".repeat(64),
      left_size_bytes: null,
      right_size_bytes: 64,
    },
  ],
  truncated: false,
  note: "file-level comparison only (path/size/sha256)",
};

async function stubWorkspace(page: Page, options: { unconfigured?: boolean } = {}) {
  await stubApi(page);
  const unconfigured = options.unconfigured === true;
  await page.route(`**/api/runs/${RUN_ID}/experiments`, (route) => {
    void route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(EXPERIMENTS),
    });
  });
  await page.route("**/api/runs/*/artifacts", (route) => {
    void route.fulfill({ status: 200, contentType: "application/json", body: "[]" });
  });
  await page.route(`**/api/runs/${RUN_ID}/workspace-snapshots`, (route) => {
    void route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(RECORDED),
    });
  });
  await page.route("**/api/workspace-snapshots/*/files", (route) => {
    void route.fulfill({
      status: unconfigured ? 503 : 200,
      contentType: "application/json",
      body: unconfigured
        ? JSON.stringify({ detail: "no workspace snapshot root configured" })
        : JSON.stringify(TREE_A),
    });
  });
  await page.route("**/api/workspace-snapshots/*/diff/*", (route) => {
    void route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(DIFF),
    });
  });
}

test.afterEach(() => {
  assertNoUnmatched();
});

async function openWorkspace(page: Page): Promise<void> {
  await page.goto(`/#/run/workspace?run=${RUN_ID}`);
  await expect(page.getByTestId("workspace-page")).toBeVisible();
  await expect(page.getByTestId("workspace-snapshot-panel")).toBeVisible();
}

test("渲染 run 记录的快照并标记保留状态", async ({ page }) => {
  await stubWorkspace(page);
  await openWorkspace(page);
  const panel = page.getByTestId("workspace-snapshot-panel");
  await expect(panel).toContainText("保留 2 / 记录 2");
  await expect(page.getByTestId("snapshot-record-row")).toHaveCount(2);
  await expect(panel).toContainText("aaaaaaaaaaaa…");
  await expect(panel).toContainText("EVIDENCE_BEFORE");
});

test("选择快照后渲染文件树（路径/大小/sha256）", async ({ page }) => {
  await stubWorkspace(page);
  await openWorkspace(page);
  await expect(page.getByText(/选择快照以查看文件树/)).toBeVisible();
  await page.getByLabel("选择快照").selectOption(DIGEST_A);
  const tree = page.getByTestId("snapshot-file-tree");
  await expect(tree).toBeVisible();
  await expect(tree).toContainText("notes.md");
  await expect(tree).toContainText("src/main.py");
  await expect(tree).toContainText("2 files");
  await expect(tree).toContainText("352 B");
});

test("选择两个快照后渲染文件级差异（不含内容行）", async ({ page }) => {
  await stubWorkspace(page);
  await openWorkspace(page);
  await page.getByLabel("左侧快照").selectOption(DIGEST_A);
  await page.getByLabel("右侧快照").selectOption(DIGEST_B);
  const diff = page.getByTestId("snapshot-diff");
  await expect(diff).toBeVisible();
  await expect(diff).toContainText("+1");
  await expect(diff).toContainText("~1");
  await expect(diff).toContainText("unchanged 1");
  await expect(diff).toContainText("src/util.py");
  await expect(diff).toContainText("src/main.py");
  await expect(page.getByTestId("snapshot-change-kind")).toHaveCount(2);
  await expect(diff).toContainText("file-level comparison only");
});

test("快照根未配置时显示原因而不是空树", async ({ page }) => {
  await stubWorkspace(page, { unconfigured: true });
  await openWorkspace(page);
  await page.getByLabel("选择快照").selectOption(DIGEST_A);
  await expect(page.getByTestId("snapshot-file-tree")).toHaveCount(0);
  await expect(page.getByText(/snapshot root configured/i)).toBeVisible();
});
