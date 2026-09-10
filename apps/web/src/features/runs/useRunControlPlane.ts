import { useRef, useState } from "react";

import { problemText } from "../../api/problemText";

export interface ControlPlane {
  pending: boolean;
  error: string | null;
  request: (call: () => Promise<unknown>) => Promise<void>;
}

/** 一次只允许一个进行中的控制面写操作；失败保持可见，不自动重试。 */
export function useRunControlPlane(busy: boolean, onChanged: () => void): ControlPlane {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const active = useRef(false);
  const request = async (call: () => Promise<unknown>): Promise<void> => {
    if (active.current || busy) return;
    active.current = true;
    setPending(true);
    setError(null);
    try {
      await call();
      onChanged();
    } catch (cause) {
      setError(problemText(cause, "transition failed"));
    } finally {
      active.current = false;
      setPending(false);
    }
  };
  return { pending, error, request };
}
