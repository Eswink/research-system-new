/** 保存动作 hook（拆分自 useEditorActions；含竞态与错误映射）。 */

import { useCallback } from "react";

import { draftApi } from "../../../api/draftClient";
import type { EditorAction, EditorState, ValidationIssue } from "./editorState";

export function useSaveDraft(
  state: EditorState,
  dispatch: (action: EditorAction) => void,
  seqRef: { current: number },
): () => void {
  const saveDraft = useCallback(async () => {
    const seq = ++seqRef.current;
    try {
      if (state.saved === null) {
        const created = await draftApi.create("draft", state.working);
        if (seq === seqRef.current) {
          dispatch({ type: "saved", saved: created });
        }
      } else {
        const previous = state.saved;
        const saved = await draftApi.save(previous.draft_id, state.working, previous.revision);
        if (seq === seqRef.current) {
          dispatch({ type: "saved", saved });
        }
      }
    } catch (error) {
      const status = (error as { status?: number }).status ?? 0;
      const conflict = status === 412;
      const issues: ValidationIssue[] =
        status === 422
          ? [
              {
                path: "$",
                code: "SCHEMA_INVALID",
                message: error instanceof Error ? error.message : "invalid",
              },
            ]
          : [];
      const message = error instanceof Error ? error.message : "save failed";
      dispatch({
        type: "saveFailed",
        issues,
        error: conflict ? "conflict" : message,
        conflict,
      });
    }
  }, [dispatch, state.saved, state.working]);
  return () => {
    void saveDraft();
  };
}
