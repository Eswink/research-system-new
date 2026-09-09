import { useEffect, useState } from "react";

export interface RunSelectionProps {
  initialRunId?: string;
  onRunSelected?: (runId: string) => void;
}

/** URL context owns cross-page identity; a standalone page can still query an explicit ID. */
export function useSelectedRun({ initialRunId = "", onRunSelected }: RunSelectionProps) {
  const [local, setLocal] = useState({ source: initialRunId, id: initialRunId });
  useEffect(() => {
    setLocal({ source: initialRunId, id: initialRunId });
  }, [initialRunId]);
  const runId = local.source === initialRunId ? local.id : initialRunId;
  const selectRun = (value: string) => {
    const id = value.trim();
    setLocal({ source: initialRunId, id });
    if (id !== initialRunId) onRunSelected?.(id);
  };
  return { runId, selectRun };
}
