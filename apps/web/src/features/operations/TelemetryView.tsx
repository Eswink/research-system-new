import type { RunTelemetryDto } from "../../api/types";
import { MetricCard } from "../../components/charts/MetricCard";
import { PanelSection } from "../../components/PanelSection";
import { useI18n } from "../../i18n/useI18n";
import { KeyValueList } from "../shared/KeyValueList";
import styles from "../shared/LivePage.module.css";

export function TelemetryView({ telemetry }: { telemetry: RunTelemetryDto }) {
  const { language } = useI18n();
  const zh = language === "zh";
  const metrics = [
    [zh ? "任务总数" : "Tasks", telemetry.tasks.total],
    [zh ? "已完成" : "Succeeded", telemetry.tasks.succeeded],
    [
      zh ? "失败 / 取消" : "Failed / cancelled",
      `${String(telemetry.tasks.failed)} / ${String(telemetry.tasks.cancelled)}`,
    ],
    [
      zh ? "排队 / 已租赁" : "Queued / leased",
      `${String(telemetry.tasks.queued)} / ${String(telemetry.tasks.leased)}`,
    ],
  ] as const;
  return (
    <div className={styles.page} data-testid="telemetry-view">
      <div className={styles.metrics}>
        {metrics.map(([label, value]) => (
          <MetricCard
            key={label}
            label={label}
            value={value}
            sub={zh ? "后端当前任务计数" : "Current backend task count"}
          />
        ))}
      </div>
      <div className={styles.split}>
        <PanelSection title={zh ? "Canonical State 投影" : "Canonical-state projection"}>
          <KeyValueList
            fields={[
              { label: "Run", value: telemetry.run_id },
              { label: "Manifest", value: telemetry.manifest_digest ?? "NOT FROZEN" },
              { label: "Exporter config", value: telemetry.exporter_config_digest ?? "UNKNOWN" },
              { label: "Generated at", value: telemetry.generated_at },
              { label: "Other tasks", value: telemetry.tasks.other },
            ]}
          />
        </PanelSection>
        <TelemetryHealth telemetry={telemetry} />
      </div>
    </div>
  );
}

function TelemetryHealth({ telemetry }: { telemetry: RunTelemetryDto }) {
  const { language } = useI18n();
  return (
    <PanelSection title={language === "zh" ? "Outbox 与遥测出口" : "Outbox and telemetry sink"}>
      <KeyValueList
        fields={[
          { label: "Outbox pending", value: telemetry.outbox.pending ?? "UNKNOWN (not 0)" },
          { label: "Outbox status", value: telemetry.outbox.status },
          { label: "Unavailable reason", value: telemetry.outbox.unavailable_reason ?? "—" },
          { label: "Sink", value: telemetry.sink.enabled ? "ENABLED" : "DISABLED" },
          { label: "Dropped", value: telemetry.sink.dropped },
          { label: "Unlinked", value: telemetry.sink.unlinked },
          { label: "Last error", value: telemetry.sink.last_error ?? "—" },
        ]}
      />
      <p className={styles.notice}>
        {language === "zh"
          ? "遥测健康不等于业务审计完整性，不能替代正式事件或费用账本。"
          : [
              "Telemetry health is not audit completeness and cannot replace formal ",
              "events or the cost ledger.",
            ].join("")}
      </p>
    </PanelSection>
  );
}
