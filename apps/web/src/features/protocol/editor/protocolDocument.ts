/**
 * 协议草稿文档模型（PLAN-20260908-033 阶段四）。
 *
 * Form 状态 = 真实契约字段（schemas/protocol.schema.json：id/version/phases）。
 * YAML 转换走 yaml 2.8.1 的文档语法树（Document），保留注释与键序，
 * 不复制原型字符串拼接序列化；解析失败时错误上抛，不静默丢字段。
 */

import { parseDocument, type Document } from "yaml";

export const PHASE_STRATEGIES = [
  "deterministic",
  "parallel_agents",
  "map_reduce",
  "population_search",
  "iterative_optimizer",
  "single_agent",
] as const;

export const GATE_TYPES = [
  "POLICY_GATE",
  "BUDGET_GATE",
  "QUALITY_GATE",
  "HUMAN_GATE",
  "SECURITY_GATE",
  "PUBLISH_GATE",
] as const;

export type PhaseStrategy = (typeof PHASE_STRATEGIES)[number];
export type GateType = (typeof GATE_TYPES)[number];

export interface RoleRequirement {
  role: string;
  minInstances: number;
  maxInstances: number;
}

export interface StopConditions {
  maxIterations: number | null;
  budgetExhausted: boolean;
}

/** 单个 phase 的 Form 状态（与 schema phase 字段一一对应） */
export interface PhaseForm {
  id: string;
  name: string;
  strategy: PhaseStrategy;
  dependsOn: string[];
  inputs: string[];
  outputs: string[];
  requiredRoles: RoleRequirement[];
  requiredCapabilities: string[];
  taskContracts: string[];
  timeoutSeconds: number | null;
  gate: GateType | null;
  stopConditions: StopConditions | null;
}

/** 整份协议的 Form 状态 */
export interface ProtocolForm {
  id: string;
  version: string;
  phases: PhaseForm[];
}

export interface ParseOutcome {
  form: ProtocolForm | null;
  /** 解析/schema 错误（Form 模式禁止进入；文本保留在 YAML 模式） */
  error: string | null;
  /** 解析成功但字段缺失等（宽松转换仍然成功时为空） */
}

const GATE_SET: ReadonlySet<string> = new Set(GATE_TYPES);
const STRATEGY_SET: ReadonlySet<string> = new Set(PHASE_STRATEGIES);

function safeText(value: unknown): string {
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return "";
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map((item) => String(item));
}

function asRoles(value: unknown): RoleRequirement[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map((item) => {
    const record = (item ?? {}) as Record<string, unknown>;
    return {
      role: safeText(record.role),
      minInstances: Number(record.min_instances ?? 0),
      maxInstances: Number(record.max_instances ?? 0),
    };
  });
}

function asStopConditions(value: unknown): StopConditions | null {
  if (typeof value !== "object" || value === null) {
    return null;
  }
  const record = value as Record<string, unknown>;
  const max = record.max_iterations;
  return {
    maxIterations: typeof max === "number" ? max : null,
    budgetExhausted: record.budget_exhausted === true,
  };
}

function asStrategy(value: unknown): PhaseStrategy {
  const text = safeText(value);
  return STRATEGY_SET.has(text) ? (text as PhaseStrategy) : "single_agent";
}

function asGate(value: unknown): GateType | null {
  const text = safeText(value);
  return GATE_SET.has(text) ? (text as GateType) : null;
}

/** 文档树 → Form 状态（宽松读取：仅 schema 校验失败才阻断） */
export function documentToForm(doc: Document): ProtocolForm {
  const body = doc.toJS() as Record<string, unknown>;
  const phasesRaw = Array.isArray(body.phases) ? body.phases : [];
  const phases: PhaseForm[] = phasesRaw.map((item) => {
    const record = (item ?? {}) as Record<string, unknown>;
    return {
      id: safeText(record.id),
      name: safeText(record.name),
      strategy: asStrategy(record.strategy),
      dependsOn: asStringArray(record.depends_on),
      inputs: asStringArray(record.inputs),
      outputs: asStringArray(record.outputs),
      requiredRoles: asRoles(record.required_roles),
      requiredCapabilities: asStringArray(record.required_capabilities),
      taskContracts: asStringArray(record.task_contracts),
      timeoutSeconds: typeof record.timeout_seconds === "number" ? record.timeout_seconds : null,
      gate: asGate(record.gate),
      stopConditions: asStopConditions(record.stop_conditions),
    };
  });
  return {
    id: safeText(body.id),
    version: safeText(body.version),
    phases,
  };
}

/** 解析 YAML 文本：返回 Form；失败时错误信息（不丢文本） */
export function parseProtocolYaml(text: string): ParseOutcome {
  try {
    const doc = parseDocument(text, { keepSourceTokens: true });
    if (doc.errors.length > 0) {
      const first = doc.errors[0];
      if (first === undefined) {
        return { form: null, error: "YAML parse failed" };
      }
      return { form: null, error: `${first.name}: ${first.message}` };
    }
    return { form: documentToForm(doc), error: null };
  } catch (error) {
    return {
      form: null,
      error: error instanceof Error ? error.message : "YAML parse failed",
    };
  }
}
