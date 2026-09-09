import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../ModelRegistryScreen.module.css";

interface ModelRegistrySection4Props {
  t: (key: string, fallback?: string) => string;
  selected: FixtureTypes.RegisteredModel;
}

export function ModelRegistrySection4({ t, selected }: ModelRegistrySection4Props) {
  return (
    <div>
      <div className={visual.caption8}>{t("mr.section.evals")}</div>
      <div className={visual.column3}>
        {Object.entries(selected.evals).map(([k, v]) => (
          <div key={k} className={visual.row4}>
            <span className={`mono ${visual.label4 ?? ""}`}>{k}</span>
            <div className={visual.indicator}>
              {v != null && (
                <div
                  className={visual.surface10}
                  style={{
                    width: `${String(v * 100)}%`,
                    background:
                      v >= 0.9 ? "var(--success)" : v >= 0.8 ? "var(--accent)" : "var(--warn)",
                  }}
                />
              )}
            </div>
            <span
              className={`mono ${visual.label5 ?? ""}`}
              style={{ color: v == null ? "var(--fg-faint)" : "var(--fg)" }}
            >
              {v == null ? t("mr.unknown") : `${(v * 100).toFixed(1)}%`}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
