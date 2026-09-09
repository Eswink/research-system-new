import { api } from "../../../api/client";
import { draftApi } from "../../../api/draftClient";
import type {
  DryRunProjectionDto,
  PreflightReportDto,
  ProtocolDraftValidateResultDto,
  ProtocolDraftViewDto,
} from "../../../api/types";
import { canStart, type EditorAction, type EditorState } from "./editorState";

export type EditorOperation = "save" | "validate" | "preflight" | "start";
export type EditorCommandResult =
  | { kind: "saved"; saved: ProtocolDraftViewDto }
  | { kind: "validated"; text: string; result: ProtocolDraftValidateResultDto }
  | { kind: "preflight"; text: string; report: PreflightReportDto; projection: DryRunProjectionDto }
  | { kind: "started"; runId: string };

export function permitsEditorOperation(
  operation: EditorOperation,
  state: EditorState,
  ackWarnings: boolean,
) {
  if (state.busy) return false;
  if (operation === "start")
    return canStart(state) && (state.preflight?.report.status !== "WARN" || ackWarnings);
  if (operation === "preflight")
    return state.sourcePath !== null && state.working === state.sourceText;
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
      const source = controlledSource(state);
      const [report, projection] = await Promise.all([
        api.compileAndPreflight(source),
        api.dryRun(source),
      ]);
      return { kind: "preflight", text: state.working, report, projection };
    }
    case "start":
      return { kind: "started", runId: (await api.startRun(controlledSource(state))).id };
    default: {
      const exhaustive: never = operation;
      throw new Error(String(exhaustive));
    }
  }
}

function controlledSource(state: EditorState): string {
  if (state.sourcePath === null || state.sourceText !== state.working) {
    throw new Error(
      "No draft-revision preflight/start API: an unchanged controlled template is required",
    );
  }
  return state.sourcePath;
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
