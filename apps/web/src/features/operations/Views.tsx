import type { CostViewDto, RunTelemetryDto, TrendViewDto } from "../../api/types";

/**
 * Operations 只读视图:全部数值来自 API 投影(五状态 cost / 分段 trend /
 * canonical telemetry summary);浏览器不做任何计算、不发明阈值。
 */

const minorAmountText = (minorUnits: number | null, currency: string | null): string => {
  if (minorUnits === null) {
    return "n/a";
  }
  return `${String(minorUnits)} ${currency ?? "currency unavailable"} minor units`;
};

export function TelemetryView({ telemetry }: { telemetry: RunTelemetryDto }) {
  return (
    <div className="operations-telemetry" data-testid="telemetry-view">
      <h3>Telemetry Summary</h3>
      <p>
        tasks: {telemetry.tasks.total} (succeeded {telemetry.tasks.succeeded}, failed{" "}
        {telemetry.tasks.failed}, cancelled {telemetry.tasks.cancelled}, queued{" "}
        {telemetry.tasks.queued}, leased {telemetry.tasks.leased})
      </p>
      <p>
        manifest: {telemetry.manifest_digest ?? "not frozen"} · exporter config:{" "}
        {telemetry.exporter_config_digest ?? "unavailable"}
      </p>
      <p>
        outbox pending: {telemetry.outbox.pending ?? "unknown"} ({telemetry.outbox.status})
      </p>
      <p>
        telemetry sink: {telemetry.sink.enabled ? "on" : "off"}; dropped{" "}
        {String(telemetry.sink.dropped)}; unlinked {String(telemetry.sink.unlinked)}
        {telemetry.sink.last_error === null ? "" : `; last error: ${telemetry.sink.last_error}`}
      </p>
      <p className="muted">generated at {telemetry.generated_at}</p>
    </div>
  );
}

export function CostView({ cost }: { cost: CostViewDto }) {
  return (
    <div className="operations-cost" data-testid="cost-view">
      <h3>Cost View</h3>
      <p>
        pricing {cost.pricing_version} (digest {cost.pricing_digest.slice(0, 12)}…) ·{" "}
        {cost.pricing_frozen ? "frozen" : "not frozen"}
      </p>
      {cost.pricing_degraded_reason !== null && (
        <p className="warning" data-testid="cost-degraded">
          {cost.pricing_degraded_reason}
        </p>
      )}
      <ul>
        {cost.dimensions.map((dimension) => (
          <li key={`${dimension.dimension}/${dimension.resource_key}`}>
            {dimension.dimension}/{dimension.resource_key}: {dimension.amount.status}{" "}
            {minorAmountText(dimension.amount.minor_units, dimension.amount.currency)}{" "}
            ({dimension.entry_count} entries)
          </li>
        ))}
      </ul>
      <p>
        total: {cost.total.status} {minorAmountText(cost.total.minor_units, cost.total.currency)}
      </p>
    </div>
  );
}

export function TrendView({ trend }: { trend: TrendViewDto }) {
  return (
    <div className="operations-trend" data-testid="trend-view">
      <h3>Evaluation Trend</h3>
      {trend.truncated && <p data-testid="trend-truncated">showing a bounded recent window</p>}
      {trend.segments.length === 0 && trend.missing.length === 0 && <p>no evaluations stored</p>}
      {trend.missing.length > 0 && (
        <p data-testid="trend-missing">
          missing evaluations: {trend.missing.map((point) => point.report_digest).join(", ")}
        </p>
      )}
      {trend.segments.map((segment, index) => (
        <div key={index} data-testid={`trend-segment-${String(index)}`}>
          {segment.points.map((point) => (
            <p key={point.report_digest}>
              {point.missing ? "(missing)" : point.report_digest.slice(0, 8)} — {point.verdict}{" "}
              (pass {String(point.pass_count)}, fail {String(point.fail_count)}, infra{" "}
              {String(point.infra_error_count)}, reviewer failures{" "}
              {String(point.reviewer_failure_count)})
            </p>
          ))}
          {segment.comparisons.map((marker, markerIndex) => (
            <p key={markerIndex}>
              regression check vs previous: {marker.verdict}
              {marker.newly_regressed.length > 0
                ? ` (regressed: ${marker.newly_regressed.join(", ")})`
                : ""}
            </p>
          ))}
        </div>
      ))}
      {trend.divergences.length > 0 && (
        <div data-testid="trend-divergences">
          {trend.divergences.map((divergence, index) => (
            <p key={index}>
              segment boundary: {divergence.verdict} — {divergence.reason}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
