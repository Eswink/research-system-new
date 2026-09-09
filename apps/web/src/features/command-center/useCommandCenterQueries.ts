import { api } from "../../api/client";
import { useResource } from "../../hooks/useResource";

/** Read-only snapshots. No paid probe, fabricated live clock or implicit latest-run selection. */
export function useCommandCenterQueries(runId: string) {
  const key = runId === "" ? null : runId;
  const runs = useResource("cc-runs", () => api.listRuns());
  const cluster = useResource("cc-cluster", () => api.clusterWorkers());
  const telemetry = useResource(key, () => api.runTelemetry(runId));
  const claims = useResource(key, () => api.runClaimMap(runId));
  const usage = useResource(key, () => api.runUsage(runId));
  const experiments = useResource(key, () => api.runExperiments(runId));
  const events = useResource(key, () => api.runEvents(runId));
  return {
    runs,
    cluster,
    telemetry,
    claims,
    usage,
    experiments,
    events,
    refresh: () => {
      runs.reload();
      cluster.reload();
      telemetry.reload();
      claims.reload();
      usage.reload();
      experiments.reload();
      events.reload();
    },
  };
}
