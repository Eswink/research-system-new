/**
 * Deterministic parallel agent orchestration: shared vocabulary.
 *
 * This module owns the orchestration-side contracts only. It deliberately has
 * no dependency on `@cursor/sdk`; the SDK adapter implements the factory and
 * catalog interfaces declared here, which keeps the runner testable with fakes
 * and keeps SDK types confined to `sdk-adapter.ts`.
 */

export const MAX_PARALLEL_PER_WAVE = 3;

/** Tasks are read-only in v1; concurrent mutation of a shared worktree is out of scope. */
export type TaskMutation = "read_only";

export interface ParallelTask {
  readonly id: string;
  readonly prompt: string;
  readonly mutation: TaskMutation;
}

export interface RuntimeOptions {
  /** Absolute workspace path passed through to the SDK local agent. */
  readonly cwd: string;
  /** Model id verified against the catalog before any agent is created. */
  readonly modelId: string;
  /** Credential handed to the SDK adapter; never logged or persisted. */
  readonly apiKey: string;
  /** Aborting stops further waves and cancels in-flight runs (Ctrl+C path). */
  readonly signal: AbortSignal;
}

/** Terminal result of one run, normalized across success/failure/cancel. */
export interface RunOutcome {
  readonly status: "finished" | "error" | "cancelled";
  readonly result: string | undefined;
  /** Failure taxonomy code from the SDK (e.g. auth/rate-limit); no raw message. */
  readonly errorCode: string | undefined;
  readonly requestId: string | undefined;
  /** Model id actually used for the run, when the runtime reports it. */
  readonly resolvedModelId: string | undefined;
  readonly durationMs: number | undefined;
}

export interface RunHandle {
  readonly id: string;
  readonly requestId: string | undefined;
  wait(): Promise<RunOutcome>;
  cancel(): Promise<void>;
}

export interface AgentHandle {
  readonly agentId: string;
  send(prompt: string): Promise<RunHandle>;
  /** Release the agent; must run exactly once on every code path. */
  dispose(): Promise<void>;
}

export interface AgentFactory {
  create(task: ParallelTask, options: RuntimeOptions): Promise<AgentHandle>;
}

export interface ModelCatalogEntry {
  readonly id: string;
  readonly displayName: string;
}

export interface ModelCatalog {
  list(): Promise<readonly ModelCatalogEntry[]>;
}

export type FailureClass = "startup" | "run" | "cancelled" | "model_drift" | "preflight";

export type SummaryStatus = "finished" | "run_failed" | "cancelled" | "startup_failed";

/** Redacted per-task summary; the only shape the CLI prints by default. */
export interface AgentRunSummary {
  readonly taskId: string;
  readonly agentId: string | undefined;
  readonly runId: string | undefined;
  readonly requestId: string | undefined;
  readonly requestedModel: string;
  readonly resolvedModel: string | undefined;
  readonly status: SummaryStatus;
  readonly durationMs: number | undefined;
  readonly failureClass: FailureClass | undefined;
  /** sha256 of the final assistant text; bodies stay out of summaries. */
  readonly resultDigest: string | undefined;
  readonly resultSize: number | undefined;
  /** SDK error code / short reason; never a raw message or prompt. */
  readonly reason: string | undefined;
}

export function assertNever(value: never): never {
  throw new Error(`Unhandled variant: ${String(value)}`);
}
