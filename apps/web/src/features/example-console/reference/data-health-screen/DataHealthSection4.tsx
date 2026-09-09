import { type Dispatch, type SetStateAction } from "react";
import visual from "../DataHealthScreen.module.css";
import { DH_METRICS } from "../dhMetrics";
import { Icon } from "../Icon";
import { StatusBadge } from "../StatusBadge";

interface DataHealthSection4Props {
  t: (key: string, fallback?: string) => string;
  health: (m: (typeof DH_METRICS)[number]) => { tone: string; label: string; icon: string };
  selectedId: string;
  setSelectedId: Dispatch<SetStateAction<string>>;
}

export function DataHealthSection4({
  t,
  health,
  selectedId,
  setSelectedId,
}: DataHealthSection4Props) {
  return (
    <div className={visual.surface}>
      <div className={`row head ${visual.surface2 ?? ""}`}>
        <span>{t("dh.dataset")}</span>
        <span>{t("dh.rows")}</span>
        <span>{t("dh.drift")}</span>
        <span>{t("dh.fresh")}</span>
        <span>{t("dh.pii")}</span>
        <span>{t("dh.skew")}</span>
        <span>{t("dh.health")}</span>
      </div>
      {DH_METRICS.map((metric) => (
        <DataHealthRow
          key={metric.id}
          metric={metric}
          active={metric.id === selectedId}
          health={health(metric)}
          t={t}
          onSelect={setSelectedId}
        />
      ))}
    </div>
  );
}

function DataHealthIdentity({
  metric,
  t,
}: {
  metric: (typeof DH_METRICS)[number];
  t: DataHealthSection4Props["t"];
}) {
  return (
    <div className={`row-cell-wrap ${visual.surface4 ?? ""}`}>
      <div className={visual.label2}>{metric.dataset}</div>
      {!metric.schema_ok && (
        <div className={visual.row}>
          <Icon name="warn-tri" size={9} /> {t("dh.schemaBroken")}
        </div>
      )}
    </div>
  );
}

function DataHealthNumbers({ metric }: { metric: (typeof DH_METRICS)[number] }) {
  return (
    <>
      <span className={`mono ${visual.label3 ?? ""}`}>{metric.rows.toLocaleString()}</span>
      <span
        className={`mono ${visual.label4 ?? ""}`}
        style={{ color: metric.drift > 0.15 ? "var(--warn)" : "var(--fg)" }}
      >
        {(metric.drift * 100).toFixed(1)}%
      </span>
      <span
        className={`mono ${visual.label5 ?? ""}`}
        style={{ color: metric.freshness_d > 10 ? "var(--warn)" : "var(--fg-muted)" }}
      >
        {metric.freshness_d}d
      </span>
      <span
        className={`mono ${visual.label6 ?? ""}`}
        style={{ color: metric.pii_hits > 0 ? "var(--danger)" : "var(--fg-muted)" }}
      >
        {metric.pii_hits}
      </span>
      <span
        className={`mono ${visual.label7 ?? ""}`}
        style={{ color: metric.label_skew > 0.35 ? "var(--warn)" : "var(--fg-muted)" }}
      >
        {metric.label_skew.toFixed(2)}
      </span>
    </>
  );
}

function DataHealthRow({
  metric,
  active,
  health,
  t,
  onSelect,
}: {
  metric: (typeof DH_METRICS)[number];
  active: boolean;
  health: { tone: string; label: string; icon: string };
  t: DataHealthSection4Props["t"];
  onSelect: Dispatch<SetStateAction<string>>;
}) {
  return (
    <div
      onClick={() => {
        onSelect(metric.id);
      }}
      className={`row ${visual.surface3 ?? ""}`}
      style={{
        background: active ? "var(--bg-hover)" : undefined,
        borderLeft: `2px solid ${active ? "var(--accent)" : "transparent"}`,
      }}
    >
      <DataHealthIdentity {...{ metric, t }} />
      <DataHealthNumbers metric={metric} />
      <StatusBadge
        tone={health.tone}
        icon={health.icon}
        label={health.label}
        size="sm"
        filled={health.tone !== "neutral"}
      />
    </div>
  );
}
