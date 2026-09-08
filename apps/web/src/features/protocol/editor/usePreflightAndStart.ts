/** 预检 + 启动动作 hook（拆分自 useEditorActions）。 */

import { useCallback } from "react";

import { api } from "../../../api/client";
import type { EditorAction, EditorState } from "./editorState";

const PREFLIGHT_SOURCE = "m12_reference_research_v1.yaml";

export function usePreflightAndStart(
  state: EditorState,
  dispatch: (action: EditorAction) => void,
  seqRef: { current: number },
): { runPreflight: () => void; startRun: () => void } {
  const runPreflight = useCallback(async () => {
    const seq = ++seqRef.current;
    try {
      const [report, projection] = await Promise.all([
        api.compileAndPreflight(PREFLIGHT_SOURCE),
        api.dryRun(PREFLIGHT_SOURCE),
      ]);
      if (seq === seqRef.current) {
        dispatch({
          type: "preflight",
          context: {
            revision: state.saved?.revision ?? 0,
            digest: state.working,
            report,
            projection,
          },
          requestSeq: seq,
          currentSeq: seqRef.current,
        });
      }
    } catch (error) {
      dispatch({
        type: "preflightFailed",
        error: error instanceof Error ? error.message : "preflight failed",
      });
    }
  }, [dispatch, state.saved, state.working]);

  const startRun = useCallback(() => {
    const saved = state.saved;
    if (saved === null) {
      return;
    }
    void api.startRun({ draft_id: saved.draft_id, draft_revision: saved.revision });
  }, [state.saved]);

  return {
    runPreflight: () => {
      void runPreflight();
    },
    startRun,
  };
}
