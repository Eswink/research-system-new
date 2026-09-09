import type { EndpointHealthDto, LlmEndpointReadDto } from "../../../api/types";

export function TestStep({
  endpoint,
  health,
  busy,
  onContinue,
  onProbe,
}: {
  endpoint: LlmEndpointReadDto;
  health: EndpointHealthDto | null;
  busy: boolean;
  onContinue: () => void;
  onProbe: () => void;
}) {
  return (
    <div data-testid="wizard-test-step">
      <p>
        Endpoint <strong>{endpoint.name}</strong> created.
      </p>
      <p>
        credential: <strong>{endpoint.credential}</strong>（明文 Key 已进入服务端，不再显示）
      </p>
      {health !== null && (
        <p data-testid="wizard-health">
          Health: {health.ok ? "reachable" : "unreachable"} ·{" "}
          {health.error_category ?? "no error category"}
        </p>
      )}
      <button type="button" onClick={onContinue} disabled={busy} data-testid="wizard-continue">
        Continue to Models
      </button>
      <button type="button" onClick={onProbe} disabled={busy} data-testid="wizard-probe">
        {busy ? "Probing…" : "Probe First Model"}
      </button>
    </div>
  );
}
