/**
 * 工作区快照替身路由（PLAN-20260915-058 WP-D）。
 *
 * 默认返回一份受控快照对（两侧 digest 都在"保留中"），让页面在替身链路下渲染
 * 真实形态：能力面 → run 记录的 digest → 文件树 → 文件级 diff。
 * 用例内如需"未配置/未保留"的诚实态，覆盖对应路由即可（见 workspace-snapshots.spec.ts）。
 */

import type { StubRoute } from "./stub-routes";

export const SNAPSHOT_BEFORE = "sha256:" + "a".repeat(64);
export const SNAPSHOT_AFTER = "sha256:" + "b".repeat(64);

const RECORDED = {
  run_id: "run-stub",
  snapshots: [
    { digest: SNAPSHOT_BEFORE, recorded_as: ["EVIDENCE_BEFORE"], retained: true },
    { digest: SNAPSHOT_AFTER, recorded_as: ["EVIDENCE_AFTER"], retained: true },
  ],
  note: "these are the snapshot digests this run recorded (evidence/experiment)",
};

const TREE = {
  digest: SNAPSHOT_BEFORE,
  files: [
    { path: "notes.md", size_bytes: 24, sha256: "1".repeat(64) },
    { path: "src/main.py", size_bytes: 15, sha256: "2".repeat(64) },
  ],
  file_count: 2,
  total_bytes: 39,
  truncated: false,
};

const DIFF = {
  left_digest: SNAPSHOT_BEFORE,
  right_digest: SNAPSHOT_AFTER,
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
      left_size_bytes: 15,
      right_size_bytes: 16,
    },
    {
      path: "src/util.py",
      kind: "ADDED",
      left_sha256: null,
      right_sha256: "4".repeat(64),
      left_size_bytes: null,
      right_size_bytes: 27,
    },
  ],
  truncated: false,
  note: "file-level comparison only (path/size/sha256)",
};

export const WORKSPACE_ROUTES: readonly StubRoute[] = [
  {
    method: "GET",
    pattern: /^\/workspace-snapshots$/,
    handler: () => ({
      status: 200,
      body: {
        configured: true,
        retained_snapshots: 2,
        max_files_per_snapshot: 5000,
        note: "snapshot store is configured",
      },
    }),
  },
  {
    method: "GET",
    pattern: /^\/runs\/[^/]+\/workspace-snapshots$/,
    handler: (url) => ({
      status: 200,
      body: { ...RECORDED, run_id: url.pathname.split("/")[2] ?? RECORDED.run_id },
    }),
  },
  {
    method: "GET",
    pattern: /^\/workspace-snapshots\/[^/]+\/files$/,
    handler: () => ({ status: 200, body: TREE }),
  },
  {
    method: "GET",
    pattern: /^\/workspace-snapshots\/[^/]+\/diff\/[^/]+$/,
    handler: () => ({ status: 200, body: DIFF }),
  },
];
