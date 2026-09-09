import type { ProblemDto, Version } from "./types";

/** HTTP/Problem 细节（client 内部拆分，保持各 client 规模阈值）。 */

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

export interface RequestOptions {
  idempotencyKey?: string;
  ifMatch?: Version;
  signal?: AbortSignal;
}

function buildHeaders(init: RequestInit, options?: RequestOptions): Headers {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (options?.idempotencyKey !== undefined) {
    headers.set("Idempotency-Key", options.idempotencyKey);
  }
  if (options?.ifMatch !== undefined) {
    headers.set("If-Match", options.ifMatch);
  }
  return headers;
}

async function toApiError(response: Response, path: string): Promise<ApiError> {
  let problem: ProblemDto | undefined;
  try {
    problem = (await response.json()) as ProblemDto;
  } catch {
    problem = undefined;
  }
  return new ApiError(
    response.status,
    problem ?? {
      type: "about:blank",
      title: "Request Failed",
      status: response.status,
      detail: `HTTP ${String(response.status)}`,
      instance: path,
    },
  );
}

/** 带响应元数据（ETag）的请求结果。 */
export interface ResponseWithEtag<T> {
  data: T;
  etag: Version;
}

async function send(path: string, init: RequestInit, options?: RequestOptions): Promise<Response> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: buildHeaders(init, options),
    signal: options?.signal ?? null,
  });
  if (!response.ok) {
    throw await toApiError(response, path);
  }
  return response;
}

export async function request<T>(
  path: string,
  init: RequestInit,
  options?: RequestOptions,
): Promise<T> {
  const response = await send(path, init, options);
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

/** 返回 body + ETag（带资源版本契约的写/读）。 */
export async function requestWithEtag<T>(
  path: string,
  init: RequestInit,
  options?: RequestOptions,
): Promise<ResponseWithEtag<T>> {
  const response = await send(path, init, options);
  const data = (await response.json()) as T;
  return { data, etag: response.headers.get("etag") ?? "" };
}

/** 每次 mutating 调用生成幂等 key（重复提交重放同一响应）。 */
export function newIdempotencyKey(): string {
  return `${Date.now().toString(36)}-${crypto.randomUUID()}`;
}
