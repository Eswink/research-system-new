import { useEffect, useRef, type RefObject } from "react";

import { ApiError } from "../../../api/http";
import {
  editorResultAction,
  performEditorOperation,
  permitsEditorOperation,
  type EditorOperation,
} from "./editorCommands";
import type { EditorAction, EditorState } from "./editorState";

interface Gates {
  active: RefObject<boolean>;
  mounted: RefObject<boolean>;
  sequence: RefObject<number>;
}

function useGates(): Gates {
  const gates: Gates = { active: useRef(false), mounted: useRef(true), sequence: useRef(0) };
  const { mounted, sequence } = gates;
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      sequence.current += 1;
    };
  }, [mounted, sequence]);
  return gates;
}

interface ExecuteContext {
  operation: EditorOperation;
  state: EditorState;
  dispatch: (action: EditorAction) => void;
  gates: Gates;
  ackWarnings: boolean;
}

async function execute(context: ExecuteContext): Promise<void> {
  const { operation, state, dispatch, gates, ackWarnings } = context;
  if (gates.active.current || !permitsEditorOperation(operation, state, ackWarnings)) return;
  gates.active.current = true;
  const requestSeq = ++gates.sequence.current;
  dispatch({ type: "operationStarted", operation });
  try {
    const result = await performEditorOperation(operation, state);
    if (gates.mounted.current && requestSeq === gates.sequence.current) {
      dispatch(editorResultAction(result, requestSeq, gates.sequence.current));
    }
  } catch (cause) {
    if (gates.mounted.current) dispatch(editorErrorAction(operation, cause));
  } finally {
    gates.active.current = false;
    if (gates.mounted.current) dispatch({ type: "operationFinished" });
  }
}

/** 编辑器动作集：每个公开动作只是一次 execute 的薄封装；门禁与 can* 同源。 */
export function useEditorActions(
  state: EditorState,
  dispatch: (action: EditorAction) => void,
  ackWarnings = false,
) {
  const gates = useGates();
  const run = (operation: EditorOperation): void => {
    void execute({ operation, state, dispatch, gates, ackWarnings });
  };
  return {
    saveDraft: () => {
      run("save");
    },
    validateDraft: () => {
      run("validate");
    },
    compileCheck: () => {
      run("compile");
    },
    runPreflight: () => {
      run("preflight");
    },
    recheckPreflight: () => {
      run("recheck");
    },
    startRun: () => {
      run("start");
    },
    canPreflight: permitsEditorOperation("preflight", state, ackWarnings),
    canCompile: permitsEditorOperation("compile", state, ackWarnings),
    canRecheck: permitsEditorOperation("recheck", state, ackWarnings),
    canStartRun: permitsEditorOperation("start", state, ackWarnings),
  };
}

function editorErrorAction(operation: EditorOperation, cause: unknown): EditorAction {
  const message = cause instanceof Error ? cause.message : "Editor request failed";
  if (operation === "compile") return { type: "analysisFailed", target: "compile", error: message };
  if (operation !== "save") return { type: "analysisFailed", target: "preflight", error: message };
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
