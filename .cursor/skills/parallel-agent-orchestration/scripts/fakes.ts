import type {
  AgentFactory,
  AgentHandle,
  ParallelTask,
  RunHandle,
  RunOutcome,
  RuntimeOptions,
} from "./types.ts";

/** Test double: releases all waiters at once to prove concurrent entry. */
export class Barrier {
  private readonly waiters: (() => void)[] = [];
  private released = false;

  arrive(): Promise<void> {
    if (this.released) {
      return Promise.resolve();
    }
    return new Promise((resolve) => this.waiters.push(resolve));
  }

  release(): void {
    this.released = true;
    for (const waiter of this.waiters) {
      waiter();
    }
  }
}

export interface FakeRunWindow {
  start?: number;
  end?: number;
  cancelled: boolean;
}

interface FakeRunInit {
  barrier: Barrier;
  outcome: RunOutcome;
  runId: string;
  requestId: string;
}

export class FakeRun implements RunHandle {
  readonly id: string;
  readonly requestId: string;
  readonly window: FakeRunWindow = { cancelled: false };
  private readonly barrier: Barrier;
  private readonly outcome: RunOutcome;

  constructor(init: FakeRunInit) {
    this.barrier = init.barrier;
    this.outcome = init.outcome;
    this.id = init.runId;
    this.requestId = init.requestId;
  }

  wait(): Promise<RunOutcome> {
    this.window.start = Date.now();
    return this.barrier.arrive().then(() => {
      this.window.end = Date.now();
      return this.outcome;
    });
  }

  cancel(): Promise<void> {
    this.window.cancelled = true;
    return Promise.resolve();
  }
}

export class FakeAgent implements AgentHandle {
  readonly agentId: string;
  disposed = false;
  private readonly run: FakeRun;

  constructor(run: FakeRun, agentId: string) {
    this.run = run;
    this.agentId = agentId;
  }

  send(): Promise<RunHandle> {
    return Promise.resolve(this.run);
  }

  dispose(): Promise<void> {
    this.disposed = true;
    return Promise.resolve();
  }
}

export class FakeFactory implements AgentFactory {
  created = 0;
  readonly agents: FakeAgent[] = [];
  private readonly barrier: Barrier;
  private readonly outcomes: ReadonlyMap<string, RunOutcome | { code: string }>;

  constructor(barrier: Barrier, outcomes: ReadonlyMap<string, RunOutcome | { code: string }>) {
    this.barrier = barrier;
    this.outcomes = outcomes;
  }

  create(task: ParallelTask): Promise<AgentHandle> {
    this.created += 1;
    const script = this.outcomes.get(task.id);
    if (script !== undefined && "code" in script) {
      const error = Object.assign(new Error("simulated startup failure"), { code: script.code });
      return Promise.reject(error);
    }
    const outcome = script ?? finished();
    const run = new FakeRun({
      barrier: this.barrier,
      outcome,
      runId: `run-${task.id}`,
      requestId: `req-${task.id}`,
    });
    const agent = new FakeAgent(run, `agent-${task.id}`);
    this.agents.push(agent);
    return Promise.resolve(agent);
  }
}

export function finished(result = "ok", resolvedModelId = "model-a"): RunOutcome {
  return {
    status: "finished",
    result,
    errorCode: undefined,
    requestId: "req-unused",
    resolvedModelId,
    durationMs: 5,
  };
}

export function optionsFor(): RuntimeOptions {
  return {
    cwd: "D:/research-system",
    modelId: "model-a",
    apiKey: "test-key-not-a-real-secret",
    signal: new AbortController().signal,
  };
}

export function tasksOf(count: number): ParallelTask[] {
  return Array.from({ length: count }, (_value, index) => ({
    id: `task-${String(index + 1)}`,
    prompt: `read-only audit prompt ${String(index + 1)}`,
    mutation: "read_only" as const,
  }));
}
