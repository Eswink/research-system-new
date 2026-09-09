import { type Dispatch, type SetStateAction } from "react";
import type * as FixtureTypes from "../../fixtureTypes";
import { ForceGraph } from "../ForceGraph";
import { Icon } from "../Icon";
import { PageToolbar } from "../PageToolbar";
import visual from "../SchedulesScreen.module.css";
import { SchedulesNew } from "./SchedulesNew";
import { SchedulesSection } from "./SchedulesSection";

interface SchedulesTitleProps {
  t: (key: string, fallback?: string) => string;
  setDrawer: Dispatch<SetStateAction<{ mode?: string } | null>>;
  schedules: FixtureTypes.Schedule[];
  setSchedules: Dispatch<SetStateAction<FixtureTypes.Schedule[]>>;
  drawer: { mode?: string } | null;
}

export function SchedulesTitle({
  t,
  setDrawer,
  schedules,
  setSchedules,
  drawer,
}: SchedulesTitleProps) {
  return (
    <div className={visual.column}>
      <PageToolbar title={t("sc.title")} subtitle={t("sc.subtitle")}>
        <button
          className="btn primary sm"
          onClick={() => {
            setDrawer({});
          }}
        >
          <Icon name="plus" size={11} /> {t("sc.new")}
        </button>
      </PageToolbar>

      <SchedulesSection {...{ t, schedules, setSchedules }} />

      {/* Dependency graph */}
      <div className={`panel ${visual.panel2 ?? ""}`}>
        <div className={visual.row}>
          <Icon name="graph" size={12} />
          <span className={visual.label4}>{t("sc.depGraph")}</span>
        </div>
        <div className={visual.surface5}>
          <ForceGraph
            nodes={schedules.map((s) => ({
              id: s.id,
              label: s.name.slice(0, 26),
              group: s.enabled ? "on" : "off",
            }))}
            edges={schedules.flatMap((s) => s.depends_on.map((d) => ({ from: d, to: s.id })))}
            width={780}
            height={220}
            groupColors={{ on: "var(--accent)", off: "var(--fg-faint)" }}
          />
        </div>
      </div>

      <SchedulesNew {...{ drawer, setDrawer, t }} />
    </div>
  );
}
