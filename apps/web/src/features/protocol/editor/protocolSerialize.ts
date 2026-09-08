import { stringify } from "yaml";

import type { PhaseForm, ProtocolForm, StopConditions } from "./protocolDocument";

/**
 * Form 状态 → YAML 文本。
 * 序列化走 yaml 2.8.1（同一文档库），保证映射/列表转义正确；
 * 顶层键序固定为 schema 顺序（id/version/phases）。
 */
export function formToYaml(form: ProtocolForm): string {
  const document: Record<string, unknown> = {
    id: form.id,
    version: form.version,
    phases: form.phases.map(phaseBody),
  };
  return stringify(document, { lineWidth: 100 });
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
