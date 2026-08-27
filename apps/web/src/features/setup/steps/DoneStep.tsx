import type { ProbeResultDto } from "../../../api/types";

function ProbeDetail({ probe }: { probe: ProbeResultDto }) {
  return (
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
  );
}

/**
 * Done 步骤（M13-R1 WP-B2）：probe 失败态如实分支渲染——
 * ok=false 时显示失败 banner（error_category + redacted message），
 * CTA 变为 Retry Probe / Finish Anyway，不伪装成功外观。
 */
export function DoneStep({
  probe,
  onRetry,
  onFinish,
}: {
  probe: ProbeResultDto;
  onRetry: () => void;
  onFinish: () => void;
}) {
  const failed = !probe.ok;
  return (
    <div data-testid="wizard-done">
      <h3>Probe Result</h3>
      {failed && (
        <div data-testid="probe-failure" className="warning" role="alert">
          <p>
            Probe did not pass · {probe.error_category ?? "unknown category"} ·{" "}
            {probe.error_message_redacted ?? "no redacted detail"}
          </p>
        </div>
      )}
      <ProbeDetail probe={probe} />
      {failed ? (
        <>
          <button type="button" onClick={onRetry}>
            Retry Probe
          </button>
          <button type="button" onClick={onFinish}>
            Finish Anyway
          </button>
        </>
      ) : (
        <button type="button" onClick={onFinish}>
          Finish Setup
        </button>
      )}
    </div>
  );
}
