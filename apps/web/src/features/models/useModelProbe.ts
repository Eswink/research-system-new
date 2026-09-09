import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import type { ProbeResultDto } from "../../api/types";

/** Explicit user action only. An in-flight probe is never replayed by an effect or refresh. */
export function useModelProbe(onComplete: () => void) {
  const [result, setResult] = useState<ProbeResultDto | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [probingId, setProbingId] = useState<string | null>(null);
  const active = useRef(false);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  const probe = useCallback(
    async (modelId: string) => {
      if (active.current) return;
      active.current = true;
      setProbingId(modelId);
      setError(null);
      setResult(null);
      try {
        const next = await api.probeModel(modelId);
        if (mounted.current) {
          setResult(next);
          onComplete();
        }
      } catch (cause) {
        if (mounted.current) setError(cause instanceof Error ? cause.message : "Probe failed");
      } finally {
        active.current = false;
        if (mounted.current) setProbingId(null);
      }
    },
    [onComplete],
  );
  return { result, error, probingId, probe };
}
