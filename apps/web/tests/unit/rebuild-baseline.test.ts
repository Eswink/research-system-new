/**
 * 高保真重建失败基线（PLAN-20260908-034 T03）。
 *
 * 本文件编码 cursor plan §2.2 确认的已知问题的【修复后期望行为】。
 * 建立基线时（重建前）这些用例应当失败；重建对应能力后必须全部通过。
 * 每个用例注明对应缺陷与修复任务（T11/T13/T14/T18/T06）。
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

import { parseProtocolYaml } from "../../src/features/protocol/editor/protocolDocument";
import { applyFormEdit } from "../../src/features/protocol/editor/protocolSerialize";
import { CANONICAL_ROUTES } from "../../src/navigation/registry";

const SRC = path.join(path.dirname(fileURLToPath(import.meta.url)), "../../src");

// ── T11：空/非对象 YAML 不得崩溃 ──────────────────────────────────────────

test("baseline: empty YAML parses to empty form without crash (T11)", () => {
  const outcome = parseProtocolYaml("");
  assert.equal(outcome.error, null);
  assert.deepEqual(outcome.form, { id: "", version: "", phases: [] });
});

test("baseline: comment-only YAML parses to empty form (T11)", () => {
  const outcome = parseProtocolYaml("# 只有注释\n");
  assert.equal(outcome.error, null);
  assert.deepEqual(outcome.form, { id: "", version: "", phases: [] });
});

test("baseline: list-root YAML yields explicit error, not silent form (T11)", () => {
  const outcome = parseProtocolYaml("- a\n- b\n");
  assert.equal(outcome.form, null);
  assert.notEqual(outcome.error, null);
});

test("baseline: scalar-root YAML yields explicit error (T11)", () => {
  const outcome = parseProtocolYaml("just-a-string");
  assert.equal(outcome.form, null);
  assert.notEqual(outcome.error, null);
});

// ── T11：YAML 往返无损（注释、单数 task_contract、显式 false） ───────────

const ROUNDTRIP_YAML = [
  "# 顶部注释：参考协议",
  "id: rt_v1 # 行内注释",
  "version: 1.0.0",
  "phases:",
  "  - id: execution",
  "    strategy: single_agent",
  "    task_contract: sort_analysis_execution # 单数字段（真实 schema 允许）",
  "    stop_conditions:",
  "      budget_exhausted: false",
].join("\n");

test("baseline: roundtrip preserves comments (T11)", () => {
  const outcome = parseProtocolYaml(ROUNDTRIP_YAML);
  assert.equal(outcome.error, null);
  assert.ok(outcome.form !== null);
  const text = applyFormEdit(ROUNDTRIP_YAML, outcome.form);
  assert.match(text, /顶部注释/);
  assert.match(text, /行内注释/);
  assert.match(text, /单数字段/);
});

test("baseline: roundtrip preserves singular task_contract (T11)", () => {
  const outcome = parseProtocolYaml(ROUNDTRIP_YAML);
  assert.ok(outcome.form !== null);
  const text = applyFormEdit(ROUNDTRIP_YAML, outcome.form);
  assert.match(text, /task_contract: sort_analysis_execution/);
});

test("baseline: roundtrip preserves explicit false (T11)", () => {
  const outcome = parseProtocolYaml(ROUNDTRIP_YAML);
  assert.ok(outcome.form !== null);
  const text = applyFormEdit(ROUNDTRIP_YAML, outcome.form);
  assert.match(text, /budget_exhausted: false/);
});

// ── T14：预检不得固定示例代检 ─────────────────────────────────────────────

test("baseline: preflight hook has no fixed example source (T14)", () => {
  const source = readFileSync(
    path.join(SRC, "features/protocol/editor/usePreflightAndStart.ts"),
    "utf8",
  );
  assert.doesNotMatch(source, /PREFLIGHT_SOURCE\s*=\s*["']m12_reference_research_v1/);
  assert.doesNotMatch(source, /m12_reference_research_v1\.yaml/);
});

// ── T18：SSE 必须消费具名事件帧 ───────────────────────────────────────────

test("baseline: run event stream subscribes named SSE events (T18)", () => {
  const source = readFileSync(
    path.join(SRC, "features/runs/useRunEventStream.ts"),
    "utf8",
  );
  // 服务端只发具名 event: 帧（run_events.py）；onmessage 只收默认 message，
  // 修复必须按事件名 addEventListener（或等价机制）。
  assert.match(source, /addEventListener\(/, "must use addEventListener for named events");
  assert.match(source, /NAMED_SSE_EVENTS/, "must enumerate named SSE event types");
  assert.doesNotMatch(source, /source\.onmessage\s*=/, "must not rely on default onmessage");
});

// ── T06：33 条规范路由注册表 ──────────────────────────────────────────────

test("baseline: canonical route registry exists with 33 routes (T06)", () => {
  const routes = CANONICAL_ROUTES.map((r) => `${r.domain}/${r.page}`);
  assert.equal(routes.length, 33, `expected 33 canonical routes, got ${String(routes.length)}`);
  for (const route of [
    "plan/overview", "plan/protocol", "plan/team",
    "portfolio/projects", "portfolio/experiments", "portfolio/runs-history", "portfolio/compare",
    "run/timeline", "run/approvals", "run/workspace",
    "library/prompts", "library/datasets", "library/notebooks", "library/model-registry",
    "library/lineage", "library/endpoints", "library/setup",
    "evidence/claims",
    "insights/reports", "insights/cost-analytics",
    "ops/alerts", "ops/incidents", "ops/schedules", "ops/integrations", "ops/data-health",
    "ops/matrix", "ops/compute", "ops/observability",
    "govern/budget", "govern/audit",
    "settings/settings", "notifications/notifications", "command-center/command-center",
  ]) {
    assert.ok(routes.includes(route), `registry missing route ${route}`);
  }
});
