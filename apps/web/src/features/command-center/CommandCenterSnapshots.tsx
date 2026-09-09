import type {
  BudgetViewDto,
  ClaimMapDto,
  ClusterViewDto,
  ExperimentViewDto,
  RunDetailDto,
  RunEventDto,
  RunTelemetryDto,
} from "../../api/types";
import { Chip } from "../../components/Chip";
import { BarSeries } from "../../components/charts/BarSeries";
import { useI18n } from "../../i18n/useI18n";
import { ledgerMinorText } from "../budget/ledgerPresentation";
import { workerStateLabel, workerTone } from "../operations/workerPresentation";
import { KeyValueList } from "../shared/KeyValueList";
import styles from "./CommandCenterPage.module.css";

export function RunsSnapshot({
  runs,
  onSelect,
}: {
  runs: RunDetailDto[];
  onSelect: (id: string) => void;
}) {
  const { language } = useI18n();
  return (
    <>
      {runs.length === 0 && (
        <p className={styles.empty}>
          {language === "zh" ? "没有已登记运行" : "No registered runs"}
        </p>
      )}
      {runs.slice(0, 8).map((run) => (
        <button
          key={run.id}
          type="button"
          className={styles.row}
          onClick={() => {
            onSelect(run.id);
          }}
          aria-label={`${run.id} · ${run.state}`}
        >
          <div>
            <strong className="mono">{run.id}</strong>
            <small>{run.protocol_id}</small>
          </div>
          <Chip>{run.state}</Chip>
        </button>
      ))}
      {runs.length > 8 && (
        <p className={styles.note}>
          {language === "zh" ? "仅显示返回集合的前 8 项" : "First eight returned items shown"}
        </p>
      )}
    </>
  );
}

export function WorkerTopologySnapshot({ cluster }: { cluster: ClusterViewDto }) {
  const { language } = useI18n();
  const zh = language === "zh";
  return (
    <>
      <div className={styles.controlPlane}>CONTROL PLANE → {cluster.workers.length} REGISTERED</div>
      {cluster.workers.slice(0, 6).map((worker) => (
        <div key={worker.worker_ref} className={styles.row}>
          <div>
            <span className="mono">{worker.worker_ref.slice(0, 16)}…</span>
            <small>
              {worker.platform} · {worker.last_heartbeat ?? "UNKNOWN HEARTBEAT"}
            </small>
          </div>
          <Chip tone={workerTone(worker.state)}>{workerStateLabel(worker.state, zh)}</Chip>
        </div>
      ))}
      <p className={styles.note}>
        {zh
          ? "登记关系，最多展示 6 项；接口无地理位置，不绘制世界地图定位。"
          : [
              "Registry relationship, first six items. No geolocation API; ",
              "no map pins are fabricated.",
            ].join("")}
      </p>
    </>
  );
}

export function TelemetrySnapshot({ telemetry }: { telemetry: RunTelemetryDto }) {
  return (
    <KeyValueList
      fields={[
        { label: "Tasks", value: telemetry.tasks.total },
        {
          label: "Succeeded / failed",
          value: `${String(telemetry.tasks.succeeded)} / ${String(telemetry.tasks.failed)}`,
        },
        { label: "Outbox", value: telemetry.outbox.pending ?? "UNKNOWN" },
        { label: "Sink", value: telemetry.sink.enabled ? "ENABLED" : "DISABLED" },
        {
          label: "Dropped / unlinked",
          value: `${String(telemetry.sink.dropped)} / ${String(telemetry.sink.unlinked)}`,
        },
        { label: "Generated", value: telemetry.generated_at },
        { label: "Error", value: telemetry.sink.last_error ?? "—" },
      ]}
    />
  );
}

export function ClaimsSnapshot({ claims }: { claims: ClaimMapDto }) {
  const counts = new Map<string, number>();
  for (const claim of claims.claims) counts.set(claim.status, (counts.get(claim.status) ?? 0) + 1);
  const { language } = useI18n();
  return (
    <>
      <div className={styles.stat}>
        {claims.claims.length}
        <small>{language === "zh" ? "正式论断" : "PERSISTED CLAIMS"}</small>
      </div>
      <div className={styles.chart}>
        <BarSeries
          width={480}
          height={130}
          data={[...counts].map(([label, count]) => ({ label, values: [count] }))}
          series={[{ key: "count", color: "var(--accent)" }]}
        />
      </div>
      <p className={styles.note}>
        Unsupported: {claims.unsupported_claims.length} · Disputed:{" "}
        {claims.contradictory_claims.length}
        {claims.degraded ? " · DEGRADED" : ""}
      </p>
    </>
  );
}

export function UsageSnapshot({ usage }: { usage: BudgetViewDto }) {
  const { language } = useI18n();
  return (
    <>
      <div className={styles.amount}>
        {ledgerMinorText(usage.total_estimated_cost_minor, usage.total_currency)}
      </div>
      <KeyValueList
        fields={[
          {
            label: "Known subtotal",
            value: ledgerMinorText(usage.known_cost_subtotal_minor, usage.total_currency),
          },
          { label: "Unknown entries", value: usage.unknown_cost_entries },
          { label: "Reservations (not spending)", value: usage.reservations.length },
        ]}
      />
      <p className={styles.note}>
        {language === "zh"
          ? "没有时间序列接口，不推断消耗速率或预计耗尽时间。"
          : "No time-series API: no inferred burn rate or exhaustion forecast."}
      </p>
    </>
  );
}

export function ExperimentsSnapshot({ view }: { view: ExperimentViewDto }) {
  const { language } = useI18n();
  return (
    <>
      {view.experiments.length === 0 && (
        <p className={styles.empty}>
          {language === "zh" ? "没有实验记录" : "No experiment records"}
        </p>
      )}
      {view.experiments.slice(0, 6).map((experiment) => (
        <div key={experiment.experiment_run_id} className={styles.row}>
          <div>
            <strong className="mono">{experiment.experiment_run_id}</strong>
            <small>{experiment.image_digest ?? "UNKNOWN IMAGE"}</small>
          </div>
          <Chip>{experiment.artifact_ids.length} artifacts</Chip>
        </div>
      ))}
      <p className={styles.note}>
        {language === "zh"
          ? "最多显示 6 项；没有队列/阶段进度接口，不将记录数当作成功实验数。"
          : [
              "First six records; no queue/stage API. Record counts do not ",
              "imply successful experiments.",
            ].join("")}
      </p>
    </>
  );
}

export function EventsSnapshot({ events }: { events: RunEventDto[] }) {
  const { language } = useI18n();
  return (
    <>
      {events.length === 0 && (
        <p className={styles.empty}>{language === "zh" ? "没有正式事件" : "No persisted events"}</p>
      )}
      {events.slice(-8).map((event) => (
        <div key={event.event_id} className={styles.row}>
          <div>
            <strong>{event.type}</strong>
            <small className="mono">{event.occurred_at}</small>
          </div>
          <Chip>{event.actor}</Chip>
        </div>
      ))}
      <p className={styles.note}>
        {language === "zh"
          ? "事件游标末尾 8 项 · HTTP 查询快照，非实时推送"
          : "Last eight cursor entries · HTTP snapshot, not live push"}
      </p>
    </>
  );
}
