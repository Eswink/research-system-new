/**
 * Console e2e（PLAN-20260914-047 WP-C）：工作区制品内容 Diff。
 *
 * 确定性 API 替身 + 用例内覆盖（不改动全局 stub fixture，避免搅动 design-fidelity
 * 基线）：验证可选两侧并渲染行级 diff、不可比时给出原因而不是空 diff。
 */

import { expect, test, type Page } from "@playwright/test";

import { assertNoUnmatched, stubApi } from "./stub-api";

const RUN_ID = "run-stub-diff";

const ARTIFACTS = [
  {
    id: "task-1:stdout.txt",
    digest: "sha256:" + "1".repeat(64),
    size_bytes: 24,
    media_type: "text/plain",
    state: "ACTIVE",
    created_by: "agent",
    source_refs: ["task:task-1"],
    classification: "execution_output",
    retention_policy: null,
    created_at: "2026-09-14T00:00:00Z",
    verified: null,
  },
  {
    id: "task-1:result.json",
    digest: "sha256:" + "2".repeat(64),
    size_bytes: 32,
    media_type: "application/json",
    state: "ACTIVE",
    created_by: "agent",
    source_refs: ["task:task-1"],
    classification: "execution_result",
    retention_policy: null,
    created_at: "2026-09-14T00:00:01Z",
    verified: null,
  },
];

const EXPERIMENTS = {
  experiments: [
    {
      experiment_run_id: "exp-stub-1",
      artifact_ids: ["task-1:stdout.txt", "task-1:result.json"],
      image_digest: null,
      environment_digest: null,
      metrics: {},
      reproduction_available: false,
    },
  ],
  reproduction_note: "stub fixture: reproduction needs the original environment digest",
};

function diffBody(unavailable: boolean) {
  return {
    left_digest: "sha256:" + "1".repeat(64),
    right_digest: "sha256:" + "2".repeat(64),
    comparison: "ARTIFACT_CONTENT",
    available: !unavailable,
    identical: false,
    reason: unavailable ? "NOT_TEXT" : null,
    lines: unavailable
      ? []
      : [
          { kind: "HUNK_HEADER", text: "@@ -1 +1 @@" },
          { kind: "REMOVED", text: '-{"status": "running"}' },
          { kind: "ADDED", text: '+{"status": "succeeded"}' },
          { kind: "CONTEXT", text: "" },
        ],
    stats: { added: unavailable ? 0 : 1, removed: unavailable ? 0 : 1, context: 1 },
    truncated: false,
    note: "comparison is artifact content vs artifact content",
  };
}

async function stubWorkspace(page: Page, unavailable: boolean): Promise<void> {
  await stubApi(page);
  await page.route(`**/api/runs/${RUN_ID}/experiments`, (route) => {
    void route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(EXPERIMENTS),
    });
  });
  await page.route(`**/api/runs/${RUN_ID}/artifacts`, (route) => {
    void route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(ARTIFACTS),
    });
  });
  await page.route("**/api/artifacts/*/diff/*", (route) => {
    void route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(diffBody(unavailable)),
    });
  });
}

test.afterEach(() => {
  assertNoUnmatched();
});

async function pickBothSides(page: Page): Promise<void> {
  await page.goto(`/#/run/workspace?run=${RUN_ID}`);
  await expect(page.getByTestId("workspace-page")).toBeVisible();
  await page.getByLabel("左侧制品").selectOption("task-1:stdout.txt");
  await page.getByLabel("右侧制品").selectOption("task-1:result.json");
}

test("工作区可选两侧制品并渲染行级 diff", async ({ page }) => {
  await stubWorkspace(page, false);
  await pickBothSides(page);
  const diff = page.getByTestId("artifact-diff");
  await expect(diff).toBeVisible();
  await expect(diff).toContainText('-{"status": "running"}');
  await expect(diff).toContainText('+{"status": "succeeded"}');
  await expect(diff).toContainText("+1");
  await expect(diff).toContainText("-1");
});

test("不可比较时给出原因，不渲染空 diff", async ({ page }) => {
  await stubWorkspace(page, true);
  await pickBothSides(page);
  await expect(page.getByText(/不可比较/)).toBeVisible();
  await expect(page.getByText(/二进制或非 UTF-8/)).toBeVisible();
  await expect(page.getByTestId("artifact-diff")).toHaveCount(0);
});
