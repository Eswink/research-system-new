/**
 * 协议编辑器状态机（PLAN-20260908-033 阶段四）。
 *
 * 状态分离：本地草稿（working）≠ 最近服务端保存（saved）≠ 保存中/冲突。
 * 只有 API 成功返回后才显示"已保存"；迟到响应通过请求序号丢弃，
 * 不能覆盖新草稿。预检结果校验其修订引用，过期报告标记 stale。
 */

import type {
  DryRunProjectionDto,
  PreflightReportDto,
  ProtocolDraftViewDto,
} from "../../../api/types";

export type EditorMode = "form" | "yaml";

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
  saveStatus: SaveStatus;
  issues: ValidationIssue[];
  preflight: PreflightContext | null;
  preflightStale: boolean;
  busy: boolean;
  error: string | null;
}

export function initialEditorState(working: string): EditorState {
  return {
    mode: "form",
    working,
    saved: null,
    saveStatus: "idle",
    issues: [],
    preflight: null,
    preflightStale: false,
    busy: false,
    error: null,
  };
}

/** working 是否与最近保存正文一致 */
export function isDirty(state: EditorState): boolean {
  if (state.saved === null) {
    return state.working.trim().length > 0;
  }
  return state.working !== state.saved.yaml_text;
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

/** 启动门禁：无未应用修改、无待完成保存/校验、报告匹配当前修订（P1） */
export function canStart(state: EditorState): boolean {
  if (state.saved === null || state.preflight === null || state.preflightStale) {
    return false;
  }
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
  | { type: "edit"; text: string }
  | { type: "mode"; mode: EditorMode }
  | { type: "saved"; saved: ProtocolDraftViewDto }
  | { type: "saveFailed"; issues: ValidationIssue[]; error: string | null; conflict: boolean }
  | { type: "preflight"; context: PreflightContext; requestSeq: number; currentSeq: number }
  | { type: "preflightFailed"; error: string }
  | { type: "reset"; working: string; saved: ProtocolDraftViewDto | null };
