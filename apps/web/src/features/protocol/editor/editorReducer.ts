import type { PreflightReportDto } from "../../../api/types";
import {
  initialEditorState,
  preflightIsStale,
  type EditorAction,
  type EditorOperation,
  type EditorState,
} from "./editorState";

export function editorReducer(state: EditorState, action: EditorAction): EditorState {
  switch (action.type) {
    case "edit":
      return applyEdit(state, action.text);
    case "loadTemplate":
      return {
        ...initialEditorState(action.text),
        sourcePath: action.sourcePath,
        sourceText: action.text,
        mode: state.mode,
      };
    case "mode":
      return { ...state, mode: action.mode };
    case "saved":
      return applySaved(state, action);
    case "operationStarted":
      return beginOperation(state, action.operation);
    case "operationFinished":
      return { ...state, busy: false };
    case "validated":
    case "compiled":
      return applyServerCheck(state, action);
    case "runStarted":
      return { ...state, startedRunId: action.runId, error: null };
    case "saveFailed":
      return applySaveFailure(state, action);
    case "preflight":
      return applyPreflight(state, action);
    case "preflightRechecked":
      return applyPreflightRecheck(state, action.text, action.report);
    case "analysisFailed":
      return applyAnalysisFailure(state, action);
    case "reset":
      return { ...initialEditorState(action.working), saved: action.saved };
    default: {
      // never exhaustiveness（architecture/require-never-default）
      const exhaustive: never = action;
      void exhaustive;
      return state;
    }
  }
}

/** 服务端 schema/编译反馈：两个动作仅字段名不同，共享分支。 */
function applyServerCheck(
  state: EditorState,
  action: Extract<EditorAction, { type: "validated" } | { type: "compiled" }>,
): EditorState {
  if (action.type === "validated") {
    return { ...state, validation: { text: action.text, result: action.result } };
  }
  return { ...state, compiled: { source: action.source, result: action.result } };
}

/** 分析类失败：compile 失败不标记预检过期；preflight 失败标记 stale。 */
function applyAnalysisFailure(
  state: EditorState,
  action: Extract<EditorAction, { type: "analysisFailed" }>,
): EditorState {
  if (action.target === "compile") {
    return { ...state, error: action.error, compiled: null };
  }
  return { ...state, error: action.error, preflightStale: true };
}

function applySaved(state: EditorState, action: Extract<EditorAction, { type: "saved" }>) {
  return {
    ...state,
    saved: action.saved,
    saveStatus: state.working === action.saved.yaml_text ? ("idle" as const) : ("dirty" as const),
    issues: [],
    error: null,
  };
}

function applySaveFailure(
  state: EditorState,
  action: Extract<EditorAction, { type: "saveFailed" }>,
) {
  return {
    ...state,
    saveStatus: action.conflict ? ("conflict" as const) : ("invalid" as const),
    issues: action.issues,
    error: action.error,
  };
}

function applyPreflight(state: EditorState, action: Extract<EditorAction, { type: "preflight" }>) {
  if (action.requestSeq !== action.currentSeq) return state;
  const next = { ...state, preflight: action.context, preflightStale: false };
  return { ...next, preflightStale: preflightIsStale(next) };
}

/** 复检查预检：只刷新报告，保留原 dry-run 投影；无既有上下文时以空投影建档。 */
function applyPreflightRecheck(state: EditorState, text: string, report: PreflightReportDto) {
  const context = {
    revision: state.preflight?.revision ?? 0,
    digest: text,
    report,
    projection: state.preflight?.projection ?? null,
  };
  return { ...state, preflight: context, preflightStale: false };
}

function beginOperation(state: EditorState, operation: EditorOperation) {
  return {
    ...state,
    busy: true,
    error: null,
    saveStatus: operation === "save" ? ("saving" as const) : state.saveStatus,
    preflight: operation === "preflight" ? null : state.preflight,
    validation: operation === "validate" ? null : state.validation,
    compiled: operation === "compile" ? null : state.compiled,
  };
}

function applyEdit(state: EditorState, text: string): EditorState {
  const next: EditorState = {
    ...state,
    working: text,
    // 编辑即脱离受控模板来源（自定义草稿：预检/启动禁用）
    sourcePath: text === state.working ? state.sourcePath : null,
    sourceText: text === state.working ? state.sourceText : null,
    saveStatus: state.saveStatus === "saving" ? state.saveStatus : "dirty",
    error: null,
  };
  next.preflightStale = preflightIsStale(next);
  return next;
}
