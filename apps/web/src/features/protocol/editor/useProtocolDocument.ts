import { useEffect, useReducer, useRef, useState } from "react";
import { draftApi } from "../../../api/draftClient";
import { useResource } from "../../../hooks/useResource";
import { editorReducer } from "./editorReducer";
import { initialEditorState, isDirty, preflightIsStale } from "./editorState";
import { useEditorActions } from "./useEditorActions";

export interface ProtocolEditorProps {
  draftId?: string | undefined;
  onDraftSaved?: ((id: string) => void) | undefined;
  onRunStarted?: ((id: string) => void) | undefined;
  /** 草稿库切换当前草稿（更新 URL context 的 draftId）。 */
  onDraftIdChange?: ((id: string) => void) | undefined;
}

/** The editor alone owns working text. URL restoration never reclassifies a draft
 * as a trusted template.
 */
export function useProtocolDocument(props: ProtocolEditorProps) {
  const [state, dispatch] = useReducer(editorReducer, initialEditorState(""));
  const [ackWarnings, setAckWarnings] = useState(false);
  const draftId = props.draftId ?? "";
  const restored = useResource(draftId === "" ? null : draftId, () => draftApi.get(draftId));
  const current = useRef(state);
  current.current = state;
  useEffect(() => {
    const data = restored.data;
    if (data !== null && data.draft_id !== current.current.saved?.draft_id) {
      dispatch({ type: "reset", working: data.yaml_text, saved: data });
    }
  }, [restored.data]);
  useEffect(() => {
    setAckWarnings(false);
  }, [state.working, state.preflight]);
  const { onDraftSaved, onRunStarted } = props;
  useEffect(() => {
    if (state.saved !== null && state.saved.draft_id !== draftId)
      onDraftSaved?.(state.saved.draft_id);
    if (state.saved === null && state.sourcePath !== null && draftId !== "") onDraftSaved?.("");
  }, [state.saved, state.sourcePath, draftId, onDraftSaved]);
  useEffect(() => {
    if (state.startedRunId !== null) onRunStarted?.(state.startedRunId);
  }, [state.startedRunId, onRunStarted]);
  const actions = useEditorActions(state, dispatch, ackWarnings);
  return {
    state,
    dispatch,
    restored,
    actions,
    ackWarnings,
    setAckWarnings,
    dirty: isDirty(state),
    stale: preflightIsStale(state),
    current,
  };
}
