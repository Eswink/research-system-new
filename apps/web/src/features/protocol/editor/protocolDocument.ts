/**
 * 协议草稿文档模型（PLAN-20260908-034 T11）。
 *
 * YAML Document 语法树是唯一编辑真相：Form 模式读取派生视图，编辑经定点修改
 * （setIn/deleteIn）写回同一棵树，序列化 = doc.toString()，因此注释、键序、
 * 未知字段、单数 task_contract、显式 false 在 Form/YAML 往返中无损保留。
 * 空文档、列表/标量根、解析错误给出明确状态，不静默默认成合法协议。
 */

import { isMap, isSeq, parseDocument, type Document } from "yaml";

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

export interface ProtocolForm {
  id: string;
  version: string;
  phases: PhaseForm[];
}

export interface ParseOutcome {
  form: ProtocolForm | null;
  doc: Document.Parsed | null;
  error: string | null;
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

/** 文档树 → Form 派生视图（只读；编辑走定点修改）。 */
export function documentToForm(doc: Document): ProtocolForm {
  const body: unknown = doc.toJS();
  const record =
    typeof body === "object" && body !== null && !Array.isArray(body)
      ? (body as Record<string, unknown>)
      : {};
  const phasesRaw = Array.isArray(record.phases) ? record.phases : [];
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
      taskContracts: taskContractList(record),
      timeoutSeconds: typeof record.timeout_seconds === "number" ? record.timeout_seconds : null,
      gate: asGate(record.gate),
      stopConditions: asStopConditions(record.stop_conditions),
    };
  });
  return {
    id: safeText(record.id),
    version: safeText(record.version),
    phases,
  };
}

/** 单数 task_contract 与复数 task_contracts 都读取，不相互覆盖。 */
function taskContractList(phase: Record<string, unknown>): string[] {
  const out: string[] = [];
  if (typeof phase.task_contract === "string") {
    out.push(phase.task_contract);
  }
  if (Array.isArray(phase.task_contracts)) {
    out.push(...phase.task_contracts.map((c) => String(c)));
  }
  return out;
}

/** 解析 YAML 文本：返回 Form + Document；非对象根/解析错误明确上抛。 */
export function parseProtocolYaml(text: string): ParseOutcome {
  try {
    const doc = parseDocument(text, { keepSourceTokens: true });
    if (doc.errors.length > 0) {
      const first = doc.errors[0];
      return {
        form: null,
        doc: null,
        error: first === undefined ? "YAML parse failed" : `${first.name}: ${first.message}`,
      };
    }
    const contents = doc.contents;
    // 空文档（null）视为合法空协议；列表/标量根为非法。
    if (contents === null) {
      return { form: { id: "", version: "", phases: [] }, doc, error: null };
    }
    if (!isMap(contents)) {
      const kind = isSeq(contents) ? "list" : "scalar";
      return { form: null, doc: null, error: `协议根必须是映射对象，当前为 ${kind}` };
    }
    return { form: documentToForm(doc), doc, error: null };
  } catch (error) {
    return {
      form: null,
      doc: null,
      error: error instanceof Error ? error.message : "YAML parse failed",
    };
  }
}

/** 无损序列化：直接输出文档树（保留注释/键序/未知字段）。 */
export function serializeDocument(doc: Document): string {
  return doc.toString({ lineWidth: 0 });
}
