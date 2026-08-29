import type { ProblemDto, Version } from "./types";

/** HTTP/Problem 细节(client 内部拆分,保持 client.ts 规模阈值)。 */

export interface ApiErrorBody extends Error {
  status: number;
  problem: ProblemDto;
}

export class ApiError extends Error implements ApiErrorBody {
  readonly status: number;
  readonly problem: ProblemDto;

  constructor(status: number, problem: ProblemDto) {
    super(problem.detail);
    this.name = "ApiError";
    this.status = status;
    this.problem = problem;
  }
}

export const API_BASE = "/api";

export async function request<T>(
  path: string,
  init: RequestInit,
  options?: { idempotencyKey?: string; ifMatch?: Version },
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (options?.idempotencyKey) {
    headers.set("Idempotency-Key", options.idempotencyKey);
  }
  if (options?.ifMatch) {
    headers.set("If-Match", options.ifMatch);
  }
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!response.ok) {
    let problem: ProblemDto | undefined;
    try {
      problem = (await response.json()) as ProblemDto;
    } catch {
      problem = undefined;
    }
    if (problem?.title) {
      throw new ApiError(response.status, problem);
    }
    throw new ApiError(response.status, {
      type: "about:blank",
      title: "Request Failed",
      status: response.status,
      detail: `HTTP ${String(response.status)}`,
      instance: path,
    });
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

/** 每次 mutating 调用生成幂等 key（重复提交重放同一响应） */
export function newIdempotencyKey(): string {
  return `${Date.now().toString(36)}-${crypto.randomUUID()}`;
}
