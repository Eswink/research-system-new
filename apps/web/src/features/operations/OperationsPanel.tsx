import { useState } from "react";

import { CostView, TelemetryView, TrendView } from "./Views";
import { useOperations } from "./useOperations";

/**
 * Operations 面板(M15):telemetry / cost / eval trend 只读投影。
 * 浏览器不做成本计算、不发明阈值、不连 telemetry vendor。
 */
export function OperationsPanel() {
  const operations = useOperations();
  const [runId, setRunId] = useState("");
  const [datasetId, setDatasetId] = useState("");

  const loadRun = () => {
    if (runId.length > 0) {
      operations.loadRun(runId).then(() => undefined, () => undefined);
    }
  };

  const loadTrend = () => {
    operations.loadTrend(datasetId.length > 0 ? datasetId : undefined).then(
      () => undefined,
      () => undefined,
    );
  };

  return (
    <section className="operations" data-testid="operations-panel">
      <h2>Operations</h2>
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
      <button type="button" onClick={loadRun} disabled={operations.busy || runId.length === 0}>
        {operations.busy ? "Loading…" : "Load Telemetry & Cost"}
      </button>
      <TrendControls
        datasetId={datasetId}
        onDatasetId={setDatasetId}
        onLoad={loadTrend}
        busy={operations.busy}
      />
      <OperationResults operations={operations} />
    </section>
  );
}

function TrendControls({
  datasetId,
  onDatasetId,
  onLoad,
  busy,
}: {
  datasetId: string;
  onDatasetId: (value: string) => void;
  onLoad: () => void;
  busy: boolean;
}) {
  return (
    <>
      <label>
        Dataset ID (optional)
        <input
          value={datasetId}
          onChange={(event) => {
            onDatasetId(event.target.value);
          }}
          placeholder="filter trend by dataset"
        />
      </label>
      <button type="button" onClick={onLoad} disabled={busy}>
        Load Evaluation Trend
      </button>
    </>
  );
}

function OperationResults({ operations }: { operations: ReturnType<typeof useOperations> }) {
  return (
    <>
      {operations.error !== null && (
        <p className="error" role="alert">
          {operations.error}
        </p>
      )}
      {operations.telemetry !== null && <TelemetryView telemetry={operations.telemetry} />}
      {operations.cost !== null && <CostView cost={operations.cost} />}
      {operations.trend !== null && <TrendView trend={operations.trend} />}
    </>
  );
}
