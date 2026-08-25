import { useState } from "react";

import { api } from "../../api/client";
import type { AgentSpecDto, DryRunProjectionDto, PreflightReportDto } from "../../api/types";

export interface DryRunState {
  report: PreflightReportDto | null;
  projection: DryRunProjectionDto | null;
  agents: AgentSpecDto[];
  busy: boolean;
  error: string | null;
  run: (protocolPath: string) => Promise<void>;
}

/** Dry-run 状态（server-state cache；刷新后重新编译，不持 Canonical State） */
export function useDryRun(): DryRunState {
  const [report, setReport] = useState<PreflightReportDto | null>(null);
  const [projection, setProjection] = useState<DryRunProjectionDto | null>(null);
  const [agents, setAgents] = useState<AgentSpecDto[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async (protocolPath: string) => {
    setBusy(true);
    setError(null);
    try {
      const [preflight, dryRun, agentList] = await Promise.all([
        api.compileAndPreflight(protocolPath),
        api.dryRun(protocolPath),
        api.listAgents(),
      ]);
      setReport(preflight);
      setProjection(dryRun);
      setAgents(agentList);
    } catch (err) {
      setError(err instanceof Error ? err.message : "dry-run failed");
    } finally {
      setBusy(false);
    }
  };

  return { report, projection, agents, busy, error, run };
}