import type { Event as ExampleEvent } from "../exampleTypes";

type Payload = ExampleEvent["payload"];
type Formatter = (payload: Payload) => string;

/** Missing fixture fields are visible UNKNOWNs, never JavaScript's "undefined". */
function field(value: string | number | undefined): string {
  return String(value ?? "UNKNOWN");
}

function taskStarted(payload: Payload): string {
  const subtasks = payload.subtasks === undefined ? "" : `(${String(payload.subtasks)} subtasks)`;
  return `${payload.phase ?? ""} ${subtasks}`;
}

function budgetReserved(payload: Payload): string {
  // The reference fixture explicitly denominates its example units in 1/100000 units.
  // This formatter is never used for a live API amount or an arbitrary currency.
  const amount =
    payload.amount_minor === undefined ? "UNKNOWN" : (payload.amount_minor / 100000).toFixed(2);
  return `${field(payload.resource)} · $${amount}`;
}

const FORMATTERS: Readonly<Record<string, Formatter>> = {
  "task.started": taskStarted,
  "agent.spawned": (p) => `${field(p.agent_id)} using ${field(p.model_id)}`,
  "tool.called": (p) => `${field(p.tool)} · model=${field(p.model_id)}`,
  "tool.returned": (p) => `${field(p.results)} results → artifact ${field(p.artifact_id)}`,
  "evidence.proposed": (p) =>
    `${field(p.relation)} ${field(p.claim_id)} @ strength ${field(p.strength)}`,
  "policy.decision": (p) => `${field(p.decision)} · ${field(p.policy_id)}`,
  "budget.reserved": budgetReserved,
  "experiment.started": (p) => `${p.experiment_run_id?.slice(0, 24) ?? "UNKNOWN"}…`,
  "task.attempt": (p) =>
    `attempt ${field(p.attempt)} · ${field(p.previous_error_class)}` +
    ` · backoff ${field(p.backoff_ms)}ms`,
  "claim.upgraded": (p) => `${field(p.claim_id)} · ${field(p.from_status)} → ${field(p.to_status)}`,
  "gate.opened": (p) => `${field(p.gate_type)} · ${field(p.reason)}`,
  "task.failed": (p) => `${field(p.error_class)} · ${field(p.error_message_redacted)}`,
};

/** Reference: screens/Timeline.jsx; EXAMPLE ONLY. Dispatch keeps event contracts independent. */
export function getEventSummary(event: ExampleEvent): string {
  return FORMATTERS[event.type]?.(event.payload) ?? "";
}
