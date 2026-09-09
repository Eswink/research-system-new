import { type Dispatch, type SetStateAction } from "react";
import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../SchedulesScreen.module.css";
import { Toggle } from "../Toggle";

interface SchedulesSection2Props {
  schedules: FixtureTypes.Schedule[];
  setSchedules: Dispatch<SetStateAction<FixtureTypes.Schedule[]>>;
  t: (key: string, fallback?: string) => string;
}

export function SchedulesSection2({ schedules, setSchedules, t }: SchedulesSection2Props) {
  return (
    <div className={visual.surface2}>
      {schedules.map((s) => (
        <div key={s.id} className={`row ${visual.surface3 ?? ""}`}>
          <span>
            <Toggle
              on={s.enabled}
              onToggle={() => {
                setSchedules((prev) =>
                  prev.map((x) => (x.id === s.id ? { ...x, enabled: !x.enabled } : x)),
                );
              }}
            />
          </span>
          <div className={`row-cell-wrap ${visual.surface4 ?? ""}`}>
            <div className={visual.label}>{s.name}</div>
            {s.depends_on.length > 0 && (
              <div className={visual.caption}>
                {t("sc.dependsOn")} {s.depends_on.join(", ")}
              </div>
            )}
          </div>
          <span className={`mono ${visual.label2 ?? ""}`}>{s.cron}</span>
          <span className={`chip ${visual.caption2 ?? ""}`}>{s.target}</span>
          <span className={`mono ${visual.caption3 ?? ""}`}>
            {s.last_run ? new Date(s.last_run).toISOString().replace("T", " ").slice(5, 16) : "—"}
          </span>
          <span
            className={`mono ${visual.caption4 ?? ""}`}
            style={{ color: s.next_run ? "var(--accent)" : "var(--fg-faint)" }}
          >
            {s.next_run
              ? new Date(s.next_run).toISOString().replace("T", " ").slice(5, 16)
              : t("sc.manual")}
          </span>
          <span
            className={`mono ${visual.label3 ?? ""}`}
            style={{ color: s.success_streak > 10 ? "var(--success)" : "var(--fg-muted)" }}
          >
            {s.success_streak} ✓
          </span>
        </div>
      ))}
    </div>
  );
}
