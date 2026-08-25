import { useState } from "react";

import { ClaimMapView, UsageView } from "./Views";
import { useInspection } from "./useInspection";

/**
 * Research Inspection 面板：Claim Map（Source → Evidence → Relation →
 * Claim）与 Budget/Usage（正式 UsageLedger truth）。
 * 只 render persisted truth；Claim 状态改变必须经过正式 use case/gate
 * （本组件只读，无 UI click → VERIFIED）。
 */
export function InspectionPanel() {
  const flow = useInspection();
  const [runId, setRunId] = useState("");

  const submit = () => {
    if (runId.length > 0) {
      flow.load(runId).then(() => undefined, () => undefined);
    }
  };

  return (
    <section className="inspection" data-testid="inspection-panel">
      <h2>Research Inspection</h2>
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
      <button type="button" onClick={submit} disabled={flow.busy || runId.length === 0}>
        {flow.busy ? "Loading…" : "Load Claims & Usage"}
      </button>
      {flow.error !== null && (
        <p className="error" role="alert">
          {flow.error}
        </p>
      )}
      {flow.claims !== null && <ClaimMapView claims={flow.claims} />}
      {flow.usage !== null && <UsageView usage={flow.usage} />}
    </section>
  );
}