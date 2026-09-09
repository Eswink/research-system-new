import { useEffect, useRef } from "react";
import { ApiError } from "../../../api/http";
import {
  editorResultAction,
  performEditorOperation,
  permitsEditorOperation,
  type EditorOperation,
} from "./editorCommands";
import type { EditorAction, EditorState } from "./editorState";

export function useEditorActions(
  state: EditorState,
  dispatch: (action: EditorAction) => void,
  ackWarnings = false,
) {
  const active = useRef(false);
  const mounted = useRef(true);
  const sequence = useRef(0);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      sequence.current += 1;
    };
  }, []);
  const execute = async (operation: EditorOperation) => {
    if (active.current || !permitsEditorOperation(operation, state, ackWarnings)) return;
    active.current = true;
    const requestSeq = ++sequence.current;
    dispatch({ type: "operationStarted", operation });
    try {
      const result = await performEditorOperation(operation, state);
      if (mounted.current && requestSeq === sequence.current) {
        dispatch(editorResultAction(result, requestSeq, sequence.current));
      }
    } catch (cause) {
      if (mounted.current) dispatch(editorErrorAction(operation, cause));
    } finally {
      active.current = false;
      if (mounted.current) dispatch({ type: "operationFinished" });
    }
  };
  return {
    saveDraft: () => {
      void execute("save");
    },
    validateDraft: () => {
      void execute("validate");
    },
    runPreflight: () => {
      void execute("preflight");
    },
    startRun: () => {
      void execute("start");
    },
    canPreflight: permitsEditorOperation("preflight", state, ackWarnings),
    canStartRun: permitsEditorOperation("start", state, ackWarnings),
  };
}

function editorErrorAction(operation: EditorOperation, cause: unknown): EditorAction {
  const message = cause instanceof Error ? cause.message : "Editor request failed";
  if (operation !== "save") return { type: "preflightFailed", error: message };
  return {
    type: "saveFailed",
    conflict: cause instanceof ApiError && cause.status === 412,
    issues:
      cause instanceof ApiError && cause.status === 422
        ? [{ path: "$", code: "SCHEMA_INVALID", message }]
        : [],
    error: message,
  };
}
