import { type Dispatch, type SetStateAction } from "react";
import visual from "../CostAnalyticsScreen.module.css";
import { Icon } from "../Icon";

interface CostAnalyticsSection3Props {
  t: (key: string, fallback?: string) => string;
  setPivot: Dispatch<SetStateAction<string>>;
  pivot: string;
}

export function CostAnalyticsSection3({ t, setPivot, pivot }: CostAnalyticsSection3Props) {
  return (
    <div className={visual.row9}>
      <Icon name="menu" size={12} />
      <span className={visual.label5}>{t("ca.pivot")}</span>
      <div className={visual.row10}>
        {(
          [
            ["model", t("ca.byModel")],
            ["project", t("ca.byProject")],
            ["task", t("ca.byTask")],
          ] as const
        ).map(([v, l]) => (
          <button
            key={v}
            onClick={() => {
              setPivot(v);
            }}
            className="btn sm ghost"
            style={{
              background: pivot === v ? "var(--bg-hover)" : "transparent",
              color: pivot === v ? "var(--fg)" : "var(--fg-muted)",
              fontWeight: pivot === v ? 500 : 400,
              borderColor: pivot === v ? "var(--border-strong)" : "transparent",
            }}
          >
            {l}
          </button>
        ))}
      </div>
    </div>
  );
}
