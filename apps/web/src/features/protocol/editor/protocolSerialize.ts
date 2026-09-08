import {
  isMap,
  isSeq,
  parseDocument,
  stringify,
  type Document,
  type YAMLMap,
} from "yaml";

import type { PhaseForm, ProtocolForm, StopConditions } from "./protocolDocument";

/**
 * Form 状态 → YAML 文本。
 *
 * 新建文档（无原文）走 yaml stringify（顶层键序 id/version/phases）。
 * 编辑既有文档必须用 applyFormEdit（文档树定点修改，保留注释/未知字段）；
 * 本函数从简化对象重新生成，不作为无损往返路径。
 */
export function formToYaml(form: ProtocolForm): string {
  const document: Record<string, unknown> = {
    id: form.id,
    version: form.version,
    phases: form.phases.map(phaseBody),
  };
  return stringify(document, { lineWidth: 0 });
}

/**
 * 把 Form 编辑应用到原文档树：逐 phase 做字段级定点修改，保留注释、键序、
 * 单数 task_contract、显式 false 与未知字段。结构变化（增删 phase）调整 seq。
 */
export function applyFormEdit(originalText: string, next: ProtocolForm): string {
  const doc = parseDocument(originalText, { keepSourceTokens: true });
  if (doc.errors.length > 0 || !isMap(doc.contents)) {
    return formToYaml(next);
  }
  const root = doc.contents as YAMLMap;
  if (next.id !== "") {
    root.set("id", next.id);
  }
  if (next.version !== "") {
    root.set("version", next.version);
  }
  syncPhases(doc, root, next.phases);
  return doc.toString({ lineWidth: 0 });
}

function syncPhases(doc: Document, root: YAMLMap, phases: readonly PhaseForm[]): void {
  const seq = root.get("phases", true);
  if (!isSeq(seq)) {
    const created = doc.createNode(phases.map(phaseBody));
    root.set("phases", created);
    return;
  }
  const list = seq;
  // 增删：调整长度（新增用完整 body；删除直接截断）
  while (list.items.length > phases.length) {
    list.items.pop();
  }
  while (list.items.length < phases.length) {
    const added = phases[list.items.length];
    if (added !== undefined) {
      list.items.push(doc.createNode(phaseBody(added)));
    }
  }
  phases.forEach((phase, i) => {
    const item = list.items[i];
    if (isMap(item)) {
      patchPhase(item, phase);
    }
  });
}

/** 单 phase 字段级定点修改（只改变化项，保留注释与未知键）。 */
function patchPhase(map: YAMLMap, phase: PhaseForm): void {
  setScalar(map, "id", phase.id);
  setScalar(map, "name", phase.name);
  setScalar(map, "strategy", phase.strategy);
  setList(map, "depends_on", phase.dependsOn);
  setList(map, "inputs", phase.inputs);
  setList(map, "outputs", phase.outputs);
  setScalar(map, "timeout_seconds", phase.timeoutSeconds);
  setScalar(map, "gate", phase.gate);
  syncStopConditions(map, phase.stopConditions);
}

/** stop_conditions 只在派生值与现有节点不同时改写，保留显式 false 等原样节点。 */
function syncStopConditions(map: YAMLMap, stop: StopConditions | null): void {
  const existing = map.get("stop_conditions");
  if (stop === null) {
    if (existing !== undefined && existing !== null) {
      map.delete("stop_conditions");
    }
    return;
  }
  if (existing !== undefined && existing !== null) {
    const current = (existing as { toJSON?: () => unknown }).toJSON?.() ?? existing;
    const record = current as Record<string, unknown>;
    const sameMax = (record.max_iterations ?? null) === stop.maxIterations;
    const sameBudget = record.budget_exhausted === stop.budgetExhausted;
    if (sameMax && sameBudget) {
      return; // 保留原节点（含显式 false 与注释）
    }
  }
  map.set("stop_conditions", stopConditionsBody(stop));
}

function setScalar(map: YAMLMap, key: string, value: unknown): void {
  if (value === null || value === undefined || value === "") {
    map.delete(key);
  } else {
    map.set(key, value);
  }
}

function setList(map: YAMLMap, key: string, items: readonly string[]): void {
  if (items.length === 0) {
    map.delete(key);
  } else {
    map.set(key, [...items]);
  }
}

/** phase Form → schema mapping（省略空字段，与 schema additionalProperties 对齐） */
function phaseBody(phase: PhaseForm): Record<string, unknown> {
  const body: Record<string, unknown> = {
    id: phase.id,
    strategy: phase.strategy,
  };
  if (phase.name !== "") {
    body.name = phase.name;
  }
  if (phase.dependsOn.length > 0) {
    body.depends_on = phase.dependsOn;
  }
  if (phase.inputs.length > 0) {
    body.inputs = phase.inputs;
  }
  if (phase.outputs.length > 0) {
    body.outputs = phase.outputs;
  }
  if (phase.requiredRoles.length > 0) {
    body.required_roles = phase.requiredRoles.map((role) => ({
      role: role.role,
      min_instances: role.minInstances,
      max_instances: role.maxInstances,
    }));
  }
  if (phase.requiredCapabilities.length > 0) {
    body.required_capabilities = phase.requiredCapabilities;
  }
  if (phase.taskContracts.length > 0) {
    body.task_contracts = phase.taskContracts;
  }
  if (phase.timeoutSeconds !== null) {
    body.timeout_seconds = phase.timeoutSeconds;
  }
  if (phase.gate !== null) {
    body.gate = phase.gate;
  }
  if (phase.stopConditions !== null) {
    body.stop_conditions = stopConditionsBody(phase.stopConditions);
  }
  return body;
}

function stopConditionsBody(stop: StopConditions): Record<string, unknown> {
  const body: Record<string, unknown> = {};
  if (stop.maxIterations !== null) {
    body.max_iterations = stop.maxIterations;
  }
  if (stop.budgetExhausted) {
    body.budget_exhausted = true;
  }
  return body;
}

export type { Document };
