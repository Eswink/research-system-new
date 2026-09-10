import { api } from "../../../api/client";
import { draftApi } from "../../../api/draftClient";
import type { ProtocolSource } from "../../../api/protocolClient";
import type {
  CompileResultDto,
  DryRunProjectionDto,
  PreflightReportDto,
  ProtocolDraftValidateResultDto,
  ProtocolDraftViewDto,
} from "../../../api/types";
import {
  canStart,
  protocolSourceOf,
  type EditorAction,
  type EditorOperation,
  type EditorState,
} from "./editorState";

export type { EditorOperation } from "./editorState";
export type EditorCommandResult =
  | { kind: "saved"; saved: ProtocolDraftViewDto }
  | { kind: "validated"; text: string; result: ProtocolDraftValidateResultDto }
  | { kind: "compiled"; source: string; result: CompileResultDto }
  | { kind: "preflight"; text: string; report: PreflightReportDto; projection: DryRunProjectionDto }
  | { kind: "rechecked"; text: string; report: PreflightReportDto }
  | { kind: "started"; runId: string };

export function permitsEditorOperation(
  operation: EditorOperation,
  state: EditorState,
  ackWarnings: boolean,
) {
  if (state.busy) return false;
  if (operation === "start")
    return canStart(state) && (state.preflight?.report.status !== "WARN" || ackWarnings);
  if (operation === "preflight" || operation === "compile") {
    return protocolSourceOf(state) !== null;
  }
  if (operation === "recheck") {
    return protocolSourceOf(state) !== null && state.preflight?.digest === state.working;
  }
  return state.working.trim() !== "";
}

/** API writes are explicit. Validation never saves, and start never substitutes
 * another template.
 */
export async function performEditorOperation(
  operation: EditorOperation,
  state: EditorState,
): Promise<EditorCommandResult> {
  switch (operation) {
    case "save":
      return {
        kind: "saved",
        saved:
          state.saved === null
            ? await draftApi.create("draft", state.working)
            : await draftApi.save(state.saved.draft_id, state.working, state.saved.revision),
      };
    case "validate":
      return {
        kind: "validated",
        text: state.working,
        result: await draftApi.validateYaml(state.working),
      };
    case "preflight": {
      const source = protocolSourceOrThrow(state);
      const [report, projection] = await Promise.all([
        api.compileAndPreflight(source),
        api.dryRun(source),
      ]);
      return { kind: "preflight", text: state.working, report, projection };
    }
    case "compile": {
      const source = protocolSourceOrThrow(state);
      const result = await api.validateProtocol(source);
      return { kind: "compiled", source: state.working, result };
    }
    case "recheck": {
      const source = protocolSourceOrThrow(state);
      return { kind: "rechecked", text: state.working, report: await api.preflight(source) };
    }
    case "start":
      return { kind: "started", runId: (await api.startRun(protocolSourceOrThrow(state))).id };
    default: {
      const exhaustive: never = operation;
      throw new Error(String(exhaustive));
    }
  }
}

/** 预检/启动的协议来源封装（定义在 editorState，共享给 canStart）。 */
function protocolSourceOrThrow(state: EditorState): ProtocolSource {
  const source = protocolSourceOf(state);
  if (source === null) {
    throw new Error("Unsaved changes: save the draft (or use an unmodified template) first");
  }
  return source;
}

export function editorResultAction(
  result: EditorCommandResult,
  requestSeq: number,
  currentSeq: number,
): EditorAction {
  switch (result.kind) {
    case "saved":
      return { type: "saved", saved: result.saved };
    case "validated":
      return { type: "validated", text: result.text, result: result.result };
    case "compiled":
      return { type: "compiled", source: result.source, result: result.result };
    case "rechecked":
      return { type: "preflightRechecked", text: result.text, report: result.report };
    case "started":
      return { type: "runStarted", runId: result.runId };
    case "preflight":
      return {
        type: "preflight",
        requestSeq,
        currentSeq,
        context: {
          revision: 0,
          digest: result.text,
          report: result.report,
          projection: result.projection,
        },
      };
    default: {
      const exhaustive: never = result;
      throw new Error(String(exhaustive));
    }
  }
}
