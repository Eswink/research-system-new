import { type Dispatch, type SetStateAction } from "react";
import visual from "../DataHealthScreen.module.css";
import { DH_METRICS } from "../dhMetrics";
import { Icon } from "../Icon";
import { MetricCard } from "../MetricCard";
import { PageToolbar } from "../PageToolbar";
import { DataHealthSection } from "./DataHealthSection";

interface DataHealthTitleProps {
  t: (key: string, fallback?: string) => string;
  health: (m: (typeof DH_METRICS)[number]) => { tone: string; label: string; icon: string };
  selectedId: string;
  setSelectedId: Dispatch<SetStateAction<string>>;
  selected:
    | {
        id: string;
        dataset: string;
        rows: number;
        drift: number;
        freshness_d: number;
        pii_hits: number;
        label_skew: number;
        schema_ok: boolean;
      }
    | undefined;
}

export function DataHealthTitle({
  t,
  health,
  selectedId,
  setSelectedId,
  selected,
}: DataHealthTitleProps) {
  return (
    <div className={visual.column}>
      <PageToolbar title={t("dh.title")} subtitle={t("dh.subtitle")}>
        <button className="btn sm">
          <Icon name="spin" size={11} /> {t("dh.rescanAll")}
        </button>
        <button className="btn primary sm">
          <Icon name="external" size={11} /> {t("dh.exportReport")}
        </button>
      </PageToolbar>

      <DataHealthTitleMHealthy {...{ t, health }} />

      <DataHealthSection {...{ t, health, selectedId, setSelectedId, selected }} />
    </div>
  );
}

interface DataHealthTitleMHealthyProps {
  t: (key: string, fallback?: string) => string;
  health: (m: (typeof DH_METRICS)[number]) => { tone: string; label: string; icon: string };
}

function DataHealthTitleMHealthy({ t, health }: DataHealthTitleMHealthyProps) {
  return (
    <div className={visual.grid}>
      <MetricCard
        label={t("dh.mHealthy")}
        value={DH_METRICS.filter((d) => health(d).label === "HEALTHY").length}
        sub={
          <span>
            / {DH_METRICS.length} {t("dh.datasets")}
          </span>
        }
      />
      <MetricCard
        label={t("dh.mDrifting")}
        value={DH_METRICS.filter((d) => d.drift > 0.15).length}
        sub={<span>{t("dh.mDriftingSub")}</span>}
        bar={DH_METRICS.filter((d) => d.drift > 0.15).length / DH_METRICS.length}
        barColor="var(--warn)"
      />
      <MetricCard
        label={t("dh.mPII")}
        value={DH_METRICS.reduce((a, d) => a + d.pii_hits, 0)}
        sub={<span>{t("dh.mPIISub")}</span>}
        barColor="var(--danger)"
      />
      <MetricCard
        label={t("dh.mStale")}
        value={DH_METRICS.filter((d) => d.freshness_d > 10).length}
        sub={<span>{t("dh.mStaleSub")}</span>}
      />
    </div>
  );
}
