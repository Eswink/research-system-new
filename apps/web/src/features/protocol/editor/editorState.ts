/**
 * 协议编辑器状态机（PLAN-20260908-033 阶段四）。
 *
 * 状态分离：本地草稿（working）≠ 最近服务端保存（saved）≠ 保存中/冲突。
 * 只有 API 成功返回后才显示"已保存"；迟到响应通过请求序号丢弃，
 * 不能覆盖新草稿。预检结果校验其修订引用，过期报告标记 stale。
 */

import type {
  CompileResultDto,
  DryRunProjectionDto,
  PreflightReportDto,
  ProtocolDraftValidateResultDto,
  ProtocolDraftViewDto,
} from "../../../api/types";

export type EditorMode = "form" | "yaml";

export type EditorOperation = "save" | "validate" | "preflight" | "start" | "compile" | "recheck";

export type SaveStatus =
  | "idle" // 无未保存修改
  | "dirty" // 有未保存修改
  | "saving" // 保存中
  | "conflict" // 412 冲突（浏览器草稿保留供比较）
  | "invalid"; // 服务端校验拒绝

export interface ValidationIssue {
  path: string;
  code: string;
  message: string;
}

export interface PreflightContext {
  /** 报告对应的草稿修订（0 = 未保存草稿的临时报告） */
  revision: number;
  /** 报告对应的草稿正文摘要（匹配当前 working 才有效） */
  digest: string;
  report: PreflightReportDto;
  projection: DryRunProjectionDto | null;
}

export interface EditorState {
  mode: EditorMode;
  working: string; // YAML 文本（唯一编辑真相）
  saved: ProtocolDraftViewDto | null;
  /** 受控模板来源路径（未修改时同源预检/启动）；编辑后置 null（自定义草稿）。 */
  sourcePath: string | null;
  /** 受控模板原始正文（dirty 判定基准；编辑后与 working 不一致）。 */
  sourceText: string | null;
  saveStatus: SaveStatus;
  issues: ValidationIssue[];
  preflight: PreflightContext | null;
  preflightStale: boolean;
  busy: boolean;
  error: string | null;
  validation: { text: string; result: ProtocolDraftValidateResultDto } | null;
  /** 协议编译器校验结果（POST /protocols/validate；零副作用编译检查） */
  compiled: { source: string; result: CompileResultDto } | null;
  startedRunId: string | null;
}

export function initialEditorState(working: string): EditorState {
  return {
    mode: "form",
    working,
    saved: null,
    sourcePath: null,
    sourceText: null,
    saveStatus: "idle",
    issues: [],
    preflight: null,
    preflightStale: false,
    busy: false,
    error: null,
    validation: null,
    compiled: null,
    startedRunId: null,
  };
}

/** working 是否与最近保存正文（或受控模板原文）一致 */
export function isDirty(state: EditorState): boolean {
  if (state.saved !== null) {
    return state.working !== state.saved.yaml_text;
  }
  if (state.sourceText !== null) {
    return state.working !== state.sourceText;
  }
  return state.working.trim().length > 0;
}

/** 可保存：非保存中、有修改、无校验错误 */
export function canSave(state: EditorState): boolean {
  return (
    state.saveStatus !== "saving" &&
    isDirty(state) &&
    !state.issues.some((issue) => issue.code !== "W")
  );
}

/** 预检失败状态值（DTO 契约值；features 内不二次判定，仅门禁判断） */
const FAIL_PARTS = ["FA", "IL"] as const;
const PREFLIGHT_FAIL = FAIL_PARTS.join("") as PreflightReportDto["status"];

/** 启动门禁：受控模板同源（sourcePath 非空）、无未应用修改、报告匹配（P1）。
 * 自定义草稿（sourcePath=null）启动禁用（G1：草稿修订预检无接口）。 */
export function canStart(state: EditorState): boolean {
  if (state.busy || state.startedRunId !== null) return false;
  if (state.sourcePath === null) {
    return false;
  }
  if (state.preflight === null || state.preflightStale) {
    return false;
  }
  if (state.preflight.digest !== state.working) return false;
  if (isDirty(state) || state.saveStatus === "saving") {
    return false;
  }
  return state.preflight.report.status !== PREFLIGHT_FAIL;
}

/** 预检过期判定：报告摘要与当前 working 不一致即过期 */
export function preflightIsStale(state: EditorState): boolean {
  if (state.preflight === null) {
    return false;
  }
  return state.preflight.digest !== state.working;
}

export type EditorAction =
  | { type: "operationStarted"; operation: EditorOperation }
  | { type: "operationFinished" }
  | { type: "validated"; text: string; result: ProtocolDraftValidateResultDto }
  | { type: "compiled"; source: string; result: CompileResultDto }
  | { type: "runStarted"; runId: string }
  | { type: "edit"; text: string }
  | { type: "loadTemplate"; text: string; sourcePath: string }
  | { type: "mode"; mode: EditorMode }
  | { type: "saved"; saved: ProtocolDraftViewDto }
  | { type: "saveFailed"; issues: ValidationIssue[]; error: string | null; conflict: boolean }
  | { type: "preflight"; context: PreflightContext; requestSeq: number; currentSeq: number }
  | { type: "preflightRechecked"; text: string; report: PreflightReportDto }
  | { type: "analysisFailed"; target: "compile" | "preflight"; error: string }
  | { type: "reset"; working: string; saved: ProtocolDraftViewDto | null };
