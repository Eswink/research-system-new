import { type Dispatch, type SetStateAction } from "react";
import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../AlertsScreen.module.css";
import { StatusBadge } from "../StatusBadge";
import { Toggle } from "../Toggle";

interface AlertsSection2Props {
  rules: FixtureTypes.AlertRule[];
  setRules: Dispatch<SetStateAction<FixtureTypes.AlertRule[]>>;
  t: (key: string, fallback?: string) => string;
}

export function AlertsSection2({ rules, setRules, t }: AlertsSection2Props) {
  return (
    <div className={visual.surface5}>
      {rules.map((r) => (
        <div key={r.id} className={`row ${visual.surface6 ?? ""}`}>
          <span>
            <Toggle
              on={r.enabled}
              onToggle={() => {
                setRules((rs) =>
                  rs.map((x) => (x.id === r.id ? { ...x, enabled: !x.enabled } : x)),
                );
              }}
            />
          </span>
          <div className={`row-cell-wrap ${visual.surface7 ?? ""}`}>
            <div className={visual.label2}>{r.name}</div>
            <div className={`mono ${visual.caption4 ?? ""}`}>{r.condition}</div>
          </div>
          <span>
            <StatusBadge
              tone={r.severity === "high" ? "danger" : r.severity === "medium" ? "warn" : "neutral"}
              label={r.severity.toUpperCase()}
              icon={r.severity === "high" ? "warn-tri" : "circle-o"}
              size="sm"
            />
          </span>
          <span className={`chip ${visual.caption5 ?? ""}`}>{r.scope}</span>
          <span className={visual.caption6}>{r.channels.join(" · ")}</span>
          <span className={`mono ${visual.caption7 ?? ""}`}>
            {r.suppress_min}
            {t("al.window")}
          </span>
          <span
            className={`mono ${visual.caption8 ?? ""}`}
            style={{ color: r.fire_count_7d > 3 ? "var(--warn)" : "var(--fg-muted)" }}
          >
            {r.fire_count_7d}×
          </span>
        </div>
      ))}
    </div>
  );
}
