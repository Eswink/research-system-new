/**
 * editorState 状态机单元测试（PLAN-20260908-033 STEP-05）。
 *
 * 覆盖：dirty 判定、canSave/canStart 启动门禁（P1）、迟到响应竞态丢弃、
 * 预检过期标记、冲突/校验失败状态、never exhaustiveness。
 */

import assert from "node:assert/strict";
import { test } from "node:test";

import type { PreflightReportDto, ProtocolDraftViewDto } from "../../src/api/types";
import {
  canSave,
  canStart,
  initialEditorState,
  isDirty,
  preflightIsStale,
} from "../../src/features/protocol/editor/editorState";
import { editorReducer } from "../../src/features/protocol/editor/editorReducer";

const YAML_V1 = "id: a_v1_0_0\nversion: 0.4.0\nphases: []\n";
const YAML_V2 = YAML_V1 + "# edited\n";

const SAVED: ProtocolDraftViewDto = {
  draft_id: "pdraft_00000001",
  project_id: "example-project",
  name: "demo",
  revision: 1,
  yaml_text: YAML_V1,
  source_digest: "sha256:aa",
  created_at: "2026-09-08T00:00:00Z",
  updated_at: "2026-09-08T00:00:00Z",
};

const REPORT: PreflightReportDto = {
  status: "PASS",
  findings: [],
  estimated_cost: null,
  estimated_cost_currency: null,
  reserved_budget_ref: null,
  unresolved_risks: [],
};

function withPreflight(state: ReturnType<typeof initialEditorState>, digest: string) {
  return { ...state, preflight: { revision: 1, digest, report: REPORT, projection: null } };
}

test("isDirty: 未保存时非空即 dirty；保存后与 saved 正文比较", () => {
  const fresh = initialEditorState("");
  assert.equal(isDirty(fresh), false);
  const editing = initialEditorState(YAML_V1);
  assert.equal(isDirty(editing), true);
  const savedState = editorReducer(editing, { type: "saved", saved: SAVED });
  assert.equal(isDirty(savedState), false);
  const edited = editorReducer(savedState, { type: "edit", text: YAML_V2 });
  assert.equal(isDirty(edited), true);
});

test("canSave: dirty 且无 error issues 才可保存；保存中禁用", () => {
  let state = editorReducer(initialEditorState(YAML_V1), { type: "saved", saved: SAVED });
  state = editorReducer(state, { type: "edit", text: YAML_V2 });
  assert.equal(canSave(state), true);
  const invalid = editorReducer(state, {
    type: "saveFailed",
    issues: [{ path: "$.id", code: "SCHEMA_INVALID", message: "bad" }],
    error: null,
    conflict: false,
  });
  assert.equal(canSave(invalid), false);
});

test("canStart: 模板或已保存修订同源 + 报告匹配才可启动；dirty/FAIL/未保存阻断（P1/WP-B）", () => {
  const base = editorReducer(initialEditorState(YAML_V1), {
    type: "loadTemplate",
    text: YAML_V1,
    sourcePath: "examples/protocols/sort_analysis_v1.yaml",
  });
  const passing = withPreflight(base, YAML_V1);
  assert.equal(canStart(passing), true);

  const dirty = editorReducer(passing, { type: "edit", text: YAML_V2 });
  assert.equal(canStart(dirty), false);

  const failing = withPreflight(base, YAML_V1);
  failing.preflight = { ...failing.preflight, report: { ...REPORT, status: "FAIL" } };
  assert.equal(canStart(failing), false);

  assert.equal(canStart(base), false); // 无预检报告

  // 未保存自定义草稿（无受控来源也无已保存修订）：即使有报告也不得启动（WP-B）。
  const custom = withPreflight(
    editorReducer(initialEditorState(YAML_V1), { type: "edit", text: YAML_V1 }),
    YAML_V1,
  );
  assert.equal(canStart(custom), false);

  // WP-B：已保存草稿修订同源 + 报告匹配 → 可启动（以 {draft_id, revision} 引用）。
  const savedBase = editorReducer(initialEditorState(YAML_V1), {
    type: "reset",
    working: SAVED.yaml_text,
    saved: SAVED,
  });
  assert.equal(canStart(withPreflight(savedBase, SAVED.yaml_text)), true);
});

test("preflightIsStale: working 变化后报告过期", () => {
  const base = editorReducer(initialEditorState(YAML_V1), { type: "saved", saved: SAVED });
  const withReport = withPreflight(base, YAML_V1);
  assert.equal(preflightIsStale(withReport), false);
  const edited = editorReducer(withReport, { type: "edit", text: YAML_V2 });
  assert.equal(preflightIsStale(edited), true);
});

test("editorReducer: 迟到预检响应被丢弃（requestSeq != currentSeq）", () => {
  const base = initialEditorState(YAML_V1);
  const context = { revision: 1, digest: YAML_V1, report: REPORT, projection: null };
  const after = editorReducer(base, { type: "preflight", context, requestSeq: 1, currentSeq: 2 });
  assert.equal(after.preflight, null);
  const applied = editorReducer(base, { type: "preflight", context, requestSeq: 2, currentSeq: 2 });
  assert.notEqual(applied.preflight, null);
});

test("editorReducer: 保存失败区分 conflict 与 invalid", () => {
  const base = editorReducer(initialEditorState(YAML_V1), { type: "edit", text: YAML_V2 });
  const conflict = editorReducer(base, {
    type: "saveFailed",
    issues: [],
    error: "revision mismatch",
    conflict: true,
  });
  assert.equal(conflict.saveStatus, "conflict");
  assert.equal(conflict.working, YAML_V2); // 浏览器草稿保留供比较
  const invalid = editorReducer(base, {
    type: "saveFailed",
    issues: [{ path: "$", code: "SCHEMA_INVALID", message: "x" }],
    error: null,
    conflict: false,
  });
  assert.equal(invalid.saveStatus, "invalid");
});

test("editorReducer: 未知 action 收敛原状态（never exhaustiveness）", () => {
  const base = initialEditorState(YAML_V1);
  const after = editorReducer(base, { type: "mode", mode: "yaml" });
  assert.equal(after.mode, "yaml");
});
