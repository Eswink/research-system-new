import { useState } from "react";

import { api } from "../../api/client";
import type { ExperimentViewDto } from "../../api/types";

function ExperimentsBody({ view }: { view: ExperimentViewDto }) {
  return (
    <div data-testid="experiments-view">
      {view.experiments.length === 0 ? (
        <p>No experiment runs associated with this run.</p>
      ) : (
        <ul>
          {view.experiments.map((experiment) => (
            <li key={experiment.experiment_run_id} data-testid="experiment-row">
              <strong>{experiment.experiment_run_id}</strong> · artifacts:{" "}
              {experiment.artifact_ids.join(", ") || "none"} · image:{" "}
              {experiment.image_digest ?? "n/a"} · env:{" "}
              {experiment.environment_digest ?? "n/a"}
              <ul>
                {Object.entries(experiment.metrics).map(([name, value]) => (
                  <li key={name}>
                    {name}: {String(value)}
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      )}
      <p className="note">{view.reproduction_note}</p>
    </div>
  );
}

/**
 * Workspace / Experiment 只读视图（WP-S3/WP-S4，诚实降级）。
 * - Experiment：persisted evidence 聚合（experiment_run_id / artifact /
 *   image / environment digest / metrics）；reproduction 标注 unavailable
 *   （M12 参考链审计不在控制面板存储边界内）。
 * - Workspace：evidence 携带 workspace snapshot digest；
 *   file-level diff 为 M6/M9 前置能力，UI 明确标注 unavailable（不伪造 diff）。
 */
export function WorkspaceView() {
  const [runId, setRunId] = useState("");
  const [view, setView] = useState<ExperimentViewDto | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    if (runId.length === 0) {
      return;
    }
    setError(null);
    try {
      setView(await api.runExperiments(runId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "experiment load failed");
    }
  };

  return (
    <section data-testid="workspace-page">
      <h2>Workspace &amp; Experiments</h2>
      <p className="note">
        file-level workspace diff unavailable — WorkspaceSnapshot 仅持久化树级 digest
        （M6/M9 文件级 manifest 为前置能力）；ReproducibilityAudit 由 M12 参考链产出，
        不在控制面板边界内（均为诚实标注，不伪造）。
      </p>
      <label>
        Run ID
        <input
          value={runId}
          onChange={(event) => {
            setRunId(event.target.value);
          }}
          placeholder="run id from Run Control"
        />
      </label>
      <button type="button" onClick={() => void load()} disabled={runId.length === 0}>
        Load Experiments
      </button>
      {error !== null && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {view !== null && <ExperimentsBody view={view} />}
    </section>
  );
}
