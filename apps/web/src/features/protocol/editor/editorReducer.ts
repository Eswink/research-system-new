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
    case "mode":
      return { ...state, mode: action.mode };
    case "saved":
      return { ...state, saved: action.saved, saveStatus: "idle", issues: [], error: null };
    case "saveFailed":
      return {
        ...state,
        saveStatus: action.conflict ? "conflict" : "invalid",
        issues: action.issues,
        error: action.error,
      };
    case "preflight": {
      // 竞态保护：仅接受最新请求的响应
      if (action.requestSeq !== action.currentSeq) {
        return state;
      }
      const next = { ...state, preflight: action.context, preflightStale: false };
      next.preflightStale = preflightIsStale(next);
      return next;
    }
    case "preflightFailed":
      return { ...state, error: action.error };
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

function applyEdit(state: EditorState, text: string): EditorState {
  const next: EditorState = {
    ...state,
    working: text,
    saveStatus: state.saveStatus === "saving" ? state.saveStatus : "dirty",
    error: null,
  };
  next.preflightStale = preflightIsStale(next);
  return next;
}
