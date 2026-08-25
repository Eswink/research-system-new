import { useState } from "react";

import { ProjectionTable } from "./ProjectionTable";
import { ReportView } from "./ReportView";
import { useDryRun } from "./useDryRun";

const PROTOCOLS = [
  "m12_reference_research_v1.yaml",
  "ai_ml_research_v0_4_0.yaml",
  "sort_analysis_v1.yaml",
];

/**
 * Dry-run 面板（END_TO_END_USER_JOURNEY §5）：展示实际 Role/Agent、
 * 模型、eligibility、Tool、Workspace/Compute、budget estimate、approvals。
 * Dry Run 零 Research side effect（后端契约保证；本组件只消费投影）。
 */
export function DryRunPanel() {
  const [protocolPath, setProtocolPath] = useState(PROTOCOLS[0] ?? "");
  const flow = useDryRun();

  const submit = () => {
    void flow.run(protocolPath);
  };

  return (
    <section className="dry-run" data-testid="dry-run-panel">
      <h2>Protocol & Dry Run</h2>
      <label>
        Protocol
        <select
          value={protocolPath}
          onChange={(event) => {
            setProtocolPath(event.target.value);
          }}
        >
          {PROTOCOLS.map((protocol) => (
            <option key={protocol} value={protocol}>
              {protocol}
            </option>
          ))}
        </select>
      </label>
      <button type="button" onClick={submit} disabled={flow.busy}>
        {flow.busy ? "Compiling…" : "Compile + Preflight + Dry Run"}
      </button>
      {flow.error !== null && (
        <p className="error" role="alert">
          {flow.error}
        </p>
      )}
      {flow.report !== null && <ReportView report={flow.report} />}
      {flow.projection !== null && (
        <ProjectionTable projection={flow.projection} agents={flow.agents} />
      )}
    </section>
  );
}