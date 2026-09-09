import {
  initialEditorState,
  preflightIsStale,
  type EditorAction,
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
      return { ...state, validation: { text: action.text, result: action.result } };
    case "runStarted":
      return { ...state, startedRunId: action.runId, error: null };
    case "saveFailed":
      return applySaveFailure(state, action);
    case "preflight":
      return applyPreflight(state, action);
    case "preflightFailed":
      return { ...state, error: action.error, preflightStale: true };
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

function beginOperation(
  state: EditorState,
  operation: "save" | "validate" | "preflight" | "start",
) {
  return {
    ...state,
    busy: true,
    error: null,
    saveStatus: operation === "save" ? ("saving" as const) : state.saveStatus,
    preflight: operation === "preflight" ? null : state.preflight,
    validation: operation === "validate" ? null : state.validation,
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
