import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "../api/http";

/**
 * 按对象隔离的资源查询状态（T09）。
 *
 * - 切换 key（Run/资源 ID）取消旧请求、丢弃迟到响应；
 * - 状态区分 loading/ready/error/forbidden/unavailable，null 不转 0；
 * - 支持局部失败：一个资源失败不影响其他资源；
 * - 查询缓存只作展示态，不充当业务真相。
 */

export type ResourcePhase = "idle" | "loading" | "ready" | "error";

export interface ResourceState<T> {
  data: T | null;
  phase: ResourcePhase;
  error: string | null;
  forbidden: boolean;
  unavailable: boolean;
  stale: boolean;
  reload: () => void;
}

function classify(err: unknown): { message: string; forbidden: boolean; unavailable: boolean } {
  if (err instanceof ApiError) {
    return {
      message: err.problem.detail || err.problem.title,
      forbidden: err.status === 403 || err.status === 401,
      unavailable: err.status === 501 || err.status === 503,
    };
  }
  return {
    message: err instanceof Error ? err.message : "request failed",
    forbidden: false,
    unavailable: false,
  };
}

interface Internal<T> {
  key: string | null;
  data: T | null;
  phase: ResourcePhase;
  error: string | null;
  forbidden: boolean;
  unavailable: boolean;
  stale: boolean;
}

const INITIAL: Internal<never> = {
  key: null,
  data: null,
  phase: "idle",
  error: null,
  forbidden: false,
  unavailable: false,
  stale: false,
};

export function useResource<T>(
  key: string | null,
  fetcher: (signal: AbortSignal) => Promise<T>,
): ResourceState<T> {
  const [internal, setInternal] = useState<Internal<T>>(INITIAL);
  const [nonce, setNonce] = useState(0);
  const generation = useRef(0);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  useEffect(() => {
    if (key === null) {
      generation.current += 1;
      setInternal(INITIAL);
      return;
    }
    return runFetch({ key, generation, fetcherRef, setInternal });
  }, [key, nonce]);

  const reload = useCallback(() => {
    setNonce((n) => n + 1);
  }, []);

  // Never expose the previous object's data during the render before an effect runs.
  const visible =
    internal.key === key
      ? internal
      : {
          ...INITIAL,
          key,
          phase: key === null ? ("idle" as const) : ("loading" as const),
        };
  return { ...visible, reload };
}

interface FetchContext<T> {
  key: string;
  generation: { current: number };
  fetcherRef: { current: (signal: AbortSignal) => Promise<T> };
  setInternal: (fn: (prev: Internal<T>) => Internal<T>) => void;
}

function runFetch<T>({ key, generation, fetcherRef, setInternal }: FetchContext<T>): () => void {
  const gen = ++generation.current;
  const controller = new AbortController();
  setInternal((prev) => ({
    ...(prev.key === key ? prev : INITIAL),
    key,
    phase: "loading",
    error: null,
    forbidden: false,
    unavailable: false,
    stale: prev.key === key && prev.data !== null,
  }));
  fetcherRef
    .current(controller.signal)
    .then((data) => {
      if (generation.current === gen && !controller.signal.aborted) {
        setInternal(() => ({
          key,
          data,
          phase: "ready",
          error: null,
          forbidden: false,
          unavailable: false,
          stale: false,
        }));
      }
    })
    .catch((err: unknown) => {
      if (generation.current !== gen || controller.signal.aborted) {
        return;
      }
      const info = classify(err);
      setInternal((prev) => ({
        ...prev,
        phase: "error",
        error: info.message,
        forbidden: info.forbidden,
        unavailable: info.unavailable,
        stale: prev.data !== null,
      }));
    });
  return () => {
    controller.abort();
  };
}
