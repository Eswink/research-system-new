import type { ProbeResultDto } from "../../../api/types";

export function DoneStep({
  probe,
  onFinish,
}: {
  probe: ProbeResultDto;
  onFinish: () => void;
}) {
  return (
    <div data-testid="wizard-done">
      <h3>Probe Result</h3>
      <dl>
        <dt>ok</dt>
        <dd>{String(probe.ok)}</dd>
        <dt>model</dt>
        <dd>{probe.returned_model_name ?? "n/a"}</dd>
        <dt>observed capabilities</dt>
        <dd>{probe.observed_capabilities.join(", ") || "none"}</dd>
        <dt>reproducibility</dt>
        <dd data-testid="probe-reproducibility">
          {probe.provider_fingerprint_available
            ? "Configuration reproducible / provider fingerprint available"
            : "Configuration reproducible / provider fingerprint unavailable"}
        </dd>
      </dl>
      <button type="button" onClick={onFinish}>
        Finish Setup
      </button>
    </div>
  );
}