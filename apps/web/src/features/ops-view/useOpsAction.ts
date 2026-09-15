import { useCallback, useState } from "react";

/** 写操作的 busy/error 状态（三个写面板共用，避免各写一遍状态机）。 */
export function useOpsAction(onDone: () => void) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const run = useCallback(
    (task: () => Promise<unknown>) => {
      if (busy) return;
      setBusy(true);
      setError(null);
      task()
        .then(() => {
          setBusy(false);
          onDone();
        })
        .catch((reason: unknown) => {
          setError(reason instanceof Error ? reason.message : String(reason));
          setBusy(false);
        });
    },
    [busy, onDone],
  );
  return { busy, error, run };
}
