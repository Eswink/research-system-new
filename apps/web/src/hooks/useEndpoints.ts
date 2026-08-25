import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { LlmEndpointReadDto } from "../api/types";

const handleError = (err: unknown): string => {
  return err instanceof Error ? err.message : "backend unavailable";
};

export interface EndpointsState {
  endpoints: LlmEndpointReadDto[];
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

/** 端点列表 server-state cache；刷新后从 API 恢复，不写 localStorage */
export function useEndpoints(): EndpointsState {
  const [endpoints, setEndpoints] = useState<LlmEndpointReadDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .listEndpoints()
      .then((items) => {
        if (!cancelled) {
          setEndpoints(items);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(handleError(err));
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const refresh = () => {
    void api.listEndpoints().then(setEndpoints);
  };

  return { endpoints, loading, error, refresh };
}
