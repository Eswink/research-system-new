/**
 * protocolDocument / protocolSerialize 转换测试（PLAN-20260908-033 STEP-05）。
 *
 * 覆盖：真实示例协议解析、Form→YAML→Form 往返不丢字段、
 * 解析失败不静默（错误返回、文本保留在 YAML 模式）、策略/门禁枚举映射。
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import {
  parseProtocolYaml,
  type ProtocolForm,
} from "../../src/features/protocol/editor/protocolDocument";
import { formToYaml } from "../../src/features/protocol/editor/protocolSerialize";

const SORT_ANALYSIS = "../../examples/protocols/sort_analysis_v1.yaml";

const MINIMAL: ProtocolForm = {
  id: "minimal_v1_0_0",
  version: "0.4.0",
  phases: [
    {
      id: "phase_a",
      name: "Alpha",
      strategy: "single_agent",
      dependsOn: [],
      inputs: [],
      outputs: ["artifact_a"],
      requiredRoles: [{ role: "experiment_engineer", minInstances: 1, maxInstances: 2 }],
      requiredCapabilities: ["workspace.read", "artifact.write"],
      taskContracts: ["contract_a"],
      timeoutSeconds: 120,
      gate: "QUALITY_GATE",
      stopConditions: { maxIterations: 3, budgetExhausted: false },
    },
  ],
};

test("parseProtocolYaml: 真实示例协议可解析", () => {
  const source = readFileSync(SORT_ANALYSIS, "utf-8");
  const outcome = parseProtocolYaml(source);
  assert.equal(outcome.error, null);
  const form = outcome.form;
  assert.notEqual(form, null);
  if (form === null) {
    return;
  }
  assert.equal(form.id, "sort_analysis_v1_0_1");
  assert.equal(form.phases.length, 2);
  const reviewPhase = form.phases[1];
  assert.notEqual(reviewPhase, undefined);
  if (reviewPhase === undefined) {
    return;
  }
  assert.equal(reviewPhase.gate, "QUALITY_GATE");
  assert.deepEqual(reviewPhase.dependsOn, ["execution"]);
});

test("formToYaml → parse 往返保留全部 schema 字段", () => {
  const text = formToYaml(MINIMAL);
  const roundtrip = parseProtocolYaml(text);
  assert.equal(roundtrip.error, null);
  const form = roundtrip.form;
  assert.notEqual(form, null);
  if (form === null) {
    return;
  }
  assert.equal(form.id, MINIMAL.id);
  assert.equal(form.version, MINIMAL.version);
  const phase = form.phases[0];
  assert.notEqual(phase, undefined);
  if (phase === undefined) {
    return;
  }
  assert.equal(phase.id, "phase_a");
  assert.equal(phase.name, "Alpha");
  assert.equal(phase.strategy, "single_agent");
  assert.deepEqual(phase.outputs, ["artifact_a"]);
  assert.deepEqual(phase.requiredRoles, MINIMAL.phases[0]?.requiredRoles);
  assert.deepEqual(phase.requiredCapabilities, ["workspace.read", "artifact.write"]);
  assert.deepEqual(phase.taskContracts, ["contract_a"]);
  assert.equal(phase.timeoutSeconds, 120);
  assert.equal(phase.gate, "QUALITY_GATE");
  assert.deepEqual(phase.stopConditions, { maxIterations: 3, budgetExhausted: false });
});

test("parseProtocolYaml: 非法 YAML 返回错误且不产 form（不静默丢字段）", () => {
  const outcome = parseProtocolYaml("id: [broken\n  bad indentation");
  assert.notEqual(outcome.error, null);
  assert.equal(outcome.form, null);
});

test("documentToForm: 未知策略/门禁回退安全值", () => {
  const outcome = parseProtocolYaml(
    "id: x_v1_0_0\nversion: 0.4.0\nphases:\n  - id: a\n    strategy: weird\n    gate: NOPE\n",
  );
  assert.equal(outcome.error, null);
  const form = outcome.form;
  assert.notEqual(form, null);
  if (form === null) {
    return;
  }
  const phase = form.phases[0];
  assert.notEqual(phase, undefined);
  if (phase === undefined) {
    return;
  }
  assert.equal(phase.strategy, "single_agent");
  assert.equal(phase.gate, null);
});
