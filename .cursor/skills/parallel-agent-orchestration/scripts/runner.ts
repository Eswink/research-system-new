import { createHash } from "node:crypto";

import { MAX_PARALLEL_PER_WAVE, assertNever } from "./types.ts";
import type {
  AgentFactory,
  AgentHandle,
  AgentRunSummary,
  ParallelTask,
  RunHandle,
  RunOutcome,
  RuntimeOptions,
} from "./types.ts";
import { splitWaves } from "./waves.ts";

export interface WaveHooks {
  /** Invoked as soon as a run handle exists, so the CLI can cancel on Ctrl+C. */
  readonly onRunStart?: (task: ParallelTask, run: RunHandle) => void;
}

/** Bundles everything a wave needs; keeps public functions at <=3 params. */
export interface WaveConfig {
  readonly options: RuntimeOptions;
  readonly hooks: WaveHooks;
}

/**
 * Run tasks in waves of at most 3 concurrent agents. A wave starts only after
 * the previous wave has fully settled and been summarized; a single task
 * failure never cancels or blocks its peers, and aborting the signal turns
 * every not-yet-started task into a cancelled summary.
 */
export async function runWaves(
  factory: AgentFactory,
  tasks: readonly ParallelTask[],
  config: WaveConfig,
): Promise<readonly AgentRunSummary[]> {
  const waves = splitWaves(tasks, MAX_PARALLEL_PER_WAVE);
  const summaries: AgentRunSummary[] = [];
  for (const wave of waves) {
    if (config.options.signal.aborted) {
      summaries.push(
        ...wave.map((task) => summaryCancelledBeforeStart(task, config.options.modelId)),
      );
      continue;
    }
    const pending = wave.map((task) => runOne(factory, task, config));
    const settled = await Promise.allSettled(pending);
    settled.forEach((result, index) => {
      const task = wave[index];
      if (task === undefined) {
        return;
      }
      if (result.status === "fulfilled") {
        summaries.push(result.value);
      } else {
        summaries.push(startupRejected(task, config.options.modelId));
      }
    });
  }
  return summaries;
}

async function runOne(
  factory: AgentFactory,
  task: ParallelTask,
  config: WaveConfig,
): Promise<AgentRunSummary> {
  const startedAt = Date.now();
  let agent: AgentHandle | undefined;
  try {
    agent = await factory.create(task, config.options);
    const run = await agent.send(task.prompt);
    config.hooks.onRunStart?.(task, run);
    const outcome = await run.wait();
    return buildSummary({
      task,
      requestedModel: config.options.modelId,
      agent,
      run,
      outcome,
      durationMs: Date.now() - startedAt,
    });
  } catch (error) {
    return startupFailure(task, config.options.modelId, { agentId: agent?.agentId, error });
  } finally {
    if (agent !== undefined) {
      await disposeQuietly(agent);
    }
  }
}

interface SummaryInput {
  readonly task: ParallelTask;
  readonly requestedModel: string;
  readonly agent: AgentHandle;
  readonly run: RunHandle;
  readonly outcome: RunOutcome;
  readonly durationMs: number;
}

function buildSummary(input: SummaryInput): AgentRunSummary {
  const { task, requestedModel, agent, run, outcome, durationMs } = input;
  const base = {
    taskId: task.id,
    agentId: agent.agentId,
    runId: run.id,
    requestId: run.requestId ?? outcome.requestId,
    requestedModel,
    resolvedModel: outcome.resolvedModelId,
    durationMs: outcome.durationMs ?? durationMs,
    resultDigest: undefined,
    resultSize: undefined,
    reason: undefined,
  };
  if (outcome.status === "finished" && isModelDrift(outcome, requestedModel)) {
    return {
      ...base,
      status: "run_failed",
      failureClass: "model_drift",
      reason: "resolved_model_mismatch",
    };
  }
  switch (outcome.status) {
    case "finished":
      return {
        ...base,
        status: "finished",
        failureClass: undefined,
        resultDigest: digestOf(outcome.result),
        resultSize: outcome.result?.length,
      };
    case "error":
      return {
        ...base,
        status: "run_failed",
        failureClass: "run",
        reason: outcome.errorCode ?? "run_error",
      };
    case "cancelled":
      return { ...base, status: "cancelled", failureClass: "cancelled", reason: "run_cancelled" };
    default:
      return assertNever(outcome.status);
  }
}

function isModelDrift(outcome: RunOutcome, requestedModel: string): boolean {
  return outcome.resolvedModelId !== undefined && outcome.resolvedModelId !== requestedModel;
}

function startupFailure(
  task: ParallelTask,
  requestedModel: string,
  failure: { agentId: string | undefined; error: unknown },
): AgentRunSummary {
  const classified = classifyThrown(failure.error);
  return {
    taskId: task.id,
    agentId: failure.agentId,
    runId: undefined,
    requestId: classified.requestId,
    requestedModel,
    resolvedModel: undefined,
    status: "startup_failed",
    durationMs: undefined,
    failureClass: "startup",
    resultDigest: undefined,
    resultSize: undefined,
    reason: classified.reason,
  };
}

function startupRejected(task: ParallelTask, requestedModel: string): AgentRunSummary {
  return {
    taskId: task.id,
    agentId: undefined,
    runId: undefined,
    requestId: undefined,
    requestedModel,
    resolvedModel: undefined,
    status: "startup_failed",
    durationMs: undefined,
    failureClass: "startup",
    resultDigest: undefined,
    resultSize: undefined,
    reason: "unhandled_rejection",
  };
}

function summaryCancelledBeforeStart(task: ParallelTask, requestedModel: string): AgentRunSummary {
  return {
    taskId: task.id,
    agentId: undefined,
    runId: undefined,
    requestId: undefined,
    requestedModel,
    resolvedModel: undefined,
    status: "cancelled",
    durationMs: undefined,
    failureClass: "cancelled",
    resultDigest: undefined,
    resultSize: undefined,
    reason: "cancelled_before_start",
  };
}

/** Never lets dispose errors mask the run result; failures surface as no-ops. */
async function disposeQuietly(agent: AgentHandle): Promise<void> {
  try {
    await agent.dispose();
  } catch {
    return;
  }
}

/** Duck-typed extraction of SDK error metadata; raw messages stay out of summaries. */
function classifyThrown(error: unknown): { reason: string; requestId: string | undefined } {
  if (typeof error !== "object" || error === null) {
    return { reason: "startup_error", requestId: undefined };
  }
  const candidate = error as Record<string, unknown>;
  const code = typeof candidate.code === "string" ? candidate.code : undefined;
  const requestId = typeof candidate.requestId === "string" ? candidate.requestId : undefined;
  return { reason: code ?? "startup_error", requestId };
}

function digestOf(text: string | undefined): string | undefined {
  if (text === undefined) {
    return undefined;
  }
  return createHash("sha256").update(text, "utf8").digest("hex");
}
