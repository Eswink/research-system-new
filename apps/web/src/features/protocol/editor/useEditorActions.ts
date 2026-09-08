/** 保存 / 预检 / 启动动作聚合 hook（含竞态序号保护）。 */

import { useRef } from "react";

import type { EditorAction, EditorState } from "./editorState";
import { useSaveDraft } from "./useSaveDraft";
import { usePreflightAndStart } from "./usePreflightAndStart";

export interface EditorActions {
  saveDraft: () => void;
  runPreflight: () => void;
  startRun: () => void;
}

export function useEditorActions(
  state: EditorState,
  dispatch: (action: EditorAction) => void,
): EditorActions {
  const seqRef = useRef(0);
  const saveDraft = useSaveDraft(state, dispatch, seqRef);
  const preflightAndStart = usePreflightAndStart(state, dispatch, seqRef);
  return {
    saveDraft,
    runPreflight: preflightAndStart.runPreflight,
    startRun: preflightAndStart.startRun,
  };
}
