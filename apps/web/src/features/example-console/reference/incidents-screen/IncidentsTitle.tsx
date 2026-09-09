import { type Dispatch, type SetStateAction } from "react";
import type * as E from "../../exampleTypes";
import { Icon } from "../Icon";
import { INCIDENTS } from "../incidents";
import visual from "../IncidentsScreen.module.css";
import { MetricCard } from "../MetricCard";
import { PageToolbar } from "../PageToolbar";
import { ViewSwitcher } from "../ViewSwitcher";
import { IncidentsSection2 } from "./IncidentsSection2";

interface IncidentsTitleProps {
  t: (key: string, fallback?: string) => string;
  statusFilter: string;
  setStatusFilter: Dispatch<SetStateAction<string>>;
  filtered: (
    | {
        id: string;
        title: string;
        severity: string;
        status: string;
        opened_at: string;
        resolved_at: string;
        duration_min: number;
        commander: string;
        scope: string[];
        impact: string;
        rca_cause: string;
        action_items: { id: string; text: string; owner: string; status: string; due: string }[];
        timeline: { at: string; event: string; actor: string }[];
      }
    | {
        id: string;
        title: string;
        severity: string;
        status: string;
        opened_at: string;
        resolved_at: null;
        duration_min: null;
        commander: string;
        scope: string[];
        impact: string;
        rca_cause: null;
        action_items: { id: string; text: string; owner: string; status: string; due: string }[];
        timeline: { at: string; event: string; actor: string }[];
      }
  )[];
  selectedId: string;
  sevMap: Record<string, { color: string; label: string; icon?: string }>;
  stMap: Record<string, E.BadgeProps>;
  setSelectedId: Dispatch<SetStateAction<string>>;
  selected:
    | {
        id: string;
        title: string;
        severity: string;
        status: string;
        opened_at: string;
        resolved_at: string;
        duration_min: number;
        commander: string;
        scope: string[];
        impact: string;
        rca_cause: string;
        action_items: { id: string; text: string; owner: string; status: string; due: string }[];
        timeline: { at: string; event: string; actor: string }[];
      }
    | {
        id: string;
        title: string;
        severity: string;
        status: string;
        opened_at: string;
        resolved_at: null;
        duration_min: null;
        commander: string;
        scope: string[];
        impact: string;
        rca_cause: null;
        action_items: { id: string; text: string; owner: string; status: string; due: string }[];
        timeline: { at: string; event: string; actor: string }[];
      }
    | undefined;
}

export function IncidentsTitle({
  t,
  statusFilter,
  setStatusFilter,
  filtered,
  selectedId,
  sevMap,
  stMap,
  setSelectedId,
  selected,
}: IncidentsTitleProps) {
  return (
    <div className={visual.column}>
      <PageToolbar title={t("ic.title")} subtitle={t("ic.subtitle")}>
        <ViewSwitcher
          value={statusFilter}
          onChange={setStatusFilter}
          views={[
            { value: "all", label: `${t("ic.all")} (${String(INCIDENTS.length)})` },
            { value: "open", label: t("ic.open") },
            { value: "postmortem", label: t("ic.postmortem") },
            { value: "resolved", label: t("ic.resolved") },
          ]}
        />
        <button className="btn primary sm">
          <Icon name="plus" size={11} /> {t("ic.declare")}
        </button>
      </PageToolbar>

      <div className={visual.grid}>
        <MetricCard
          label={t("ic.mOpen")}
          value={INCIDENTS.filter((i) => i.status === "open").length}
          sub={<span>{t("ic.mOpenSub")}</span>}
        />
        <MetricCard label={t("ic.mMTTR")} value="82m" sub={<span>{t("ic.mMTTRSub")}</span>} />
        <MetricCard label={t("ic.mMTTD")} value="4m" sub={<span>{t("ic.mMTTDSub")}</span>} />
        <MetricCard
          label={t("ic.mActions")}
          value="4 / 7"
          sub={<span>{t("ic.mActionsSub")}</span>}
          bar={4 / 7}
        />
      </div>

      <IncidentsSection2 {...{ t, filtered, selectedId, sevMap, stMap, setSelectedId, selected }} />
    </div>
  );
}
