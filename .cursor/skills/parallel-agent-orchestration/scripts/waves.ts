import { MAX_PARALLEL_PER_WAVE, assertNever } from "./types.ts";

export interface TaskValidationIssue {
  readonly taskId: string;
  readonly reason: string;
}

interface LooseTask {
  readonly id: string;
  readonly prompt: string;
  readonly mutation: string;
}

/**
 * Structural validation. Rejects duplicate ids, empty prompts and any
 * mutation other than `read_only` so a malformed task file can never reach
 * the SDK layer.
 */
export function validateTasks(tasks: readonly unknown[]): readonly TaskValidationIssue[] {
  const issues: TaskValidationIssue[] = [];
  const seenIds = new Set<string>();
  tasks.forEach((item, index) => {
    const taskId = describeTaskId(item, index);
    if (!isLooseTask(item)) {
      issues.push({ taskId, reason: "task is not {id,prompt,mutation:read_only}" });
      return;
    }
    if (seenIds.has(item.id)) {
      issues.push({ taskId: item.id, reason: "duplicate task id" });
      return;
    }
    seenIds.add(item.id);
    if (item.prompt.trim().length === 0) {
      issues.push({ taskId: item.id, reason: "prompt is empty" });
    }
    if (item.mutation !== "read_only") {
      issues.push({ taskId: item.id, reason: "only mutation=read_only is allowed" });
    }
  });
  return issues;
}

function isLooseTask(item: unknown): item is LooseTask {
  if (typeof item !== "object" || item === null) {
    return false;
  }
  const candidate = item as Record<string, unknown>;
  return (
    typeof candidate.id === "string" &&
    candidate.id.trim().length > 0 &&
    typeof candidate.prompt === "string" &&
    typeof candidate.mutation === "string"
  );
}

function describeTaskId(item: unknown, index: number): string {
  if (typeof item === "object" && item !== null) {
    const id = (item as Record<string, unknown>).id;
    if (typeof id === "string" && id.trim().length > 0) {
      return id;
    }
  }
  return `index-${String(index)}`;
}

/** Split tasks into ordered waves of at most `size`; size is capped at 3. */
export function splitWaves<T>(items: readonly T[], size: number): readonly (readonly T[])[] {
  if (!Number.isInteger(size) || size < 1 || size > MAX_PARALLEL_PER_WAVE) {
    throw new RangeError(`wave size must be an integer in 1..${String(MAX_PARALLEL_PER_WAVE)}`);
  }
  const waves: T[][] = [];
  for (let index = 0; index < items.length; index += size) {
    waves.push(items.slice(index, index + size));
  }
  return waves;
}

export function formatIssues(issues: readonly TaskValidationIssue[]): string {
  return issues.map((issue) => `${issue.taskId}: ${issue.reason}`).join("; ");
}

export { assertNever };
