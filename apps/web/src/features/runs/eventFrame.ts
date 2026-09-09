import type { RunEventDto } from "../../api/types";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function nullableText(value: unknown): value is string | null {
  return value === null || typeof value === "string";
}

/** Validate the transport envelope before rendering; never log a rejected frame's content. */
export function parseRunEventFrame(raw: string, runId: string): RunEventDto | null {
  try {
    const parsed: unknown = JSON.parse(raw);
    if (!isRecord(parsed) || parsed.run_id !== runId || !isRecord(parsed.payload)) return null;
    const fields = ["event_id", "type", "schema_version", "occurred_at", "actor", "scope"];
    if (!fields.every((key) => typeof parsed[key] === "string")) return null;
    if (parsed.event_id === "" || parsed.type === "") return null;
    if (!nullableText(parsed.task_id) || !nullableText(parsed.trace_id)) return null;
    return {
      event_id: String(parsed.event_id),
      type: String(parsed.type),
      schema_version: String(parsed.schema_version),
      occurred_at: String(parsed.occurred_at),
      actor: String(parsed.actor),
      scope: String(parsed.scope),
      run_id: runId,
      task_id: parsed.task_id,
      trace_id: parsed.trace_id,
      payload: parsed.payload,
    };
  } catch {
    return null;
  }
}
