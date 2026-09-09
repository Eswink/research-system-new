import { Icon } from "../Icon";
import visual from "../RunDiffView.module.css";

interface RunDiffViewSection3Props {
  t: (key: string, fallback?: string) => string;
  diff: {
    a: { id: string; label: string };
    b: { id: string; label: string };
    metrics: { key: string; a: number; b: number; delta: number; better: boolean; unit: string }[];
    manifest_diff: (
      | { field: string; a: string; b: string; note: string }
      | { field: string; a: number; b: number; note: string }
    )[];
  };
}

export function RunDiffViewSection3({ t, diff }: RunDiffViewSection3Props) {
  return (
    <div className={`panel ${visual.panel3 ?? ""}`}>
      <div className={visual.row4}>
        <Icon name="diamond" size={12} />
        <span className={visual.label6}>{t("rh.manifestDiff")}</span>
        <span className="chip">
          {diff.manifest_diff.filter((m) => m.a !== m.b).length} {t("rh.changed")}
        </span>
      </div>
      <div>
        {diff.manifest_diff.map((m, i) => {
          const changed = String(m.a) !== String(m.b);
          return (
            <div key={i} className={visual.grid4}>
              <span className={`mono ${visual.label7 ?? ""}`}>{m.field}</span>
              <span
                className={`mono ${visual.label8 ?? ""}`}
                style={{ color: changed ? "var(--danger)" : "var(--fg-muted)" }}
              >
                {String(m.a)}
              </span>
              <span className={visual.surface8}>{changed ? "→" : "="}</span>
              <span
                className={`mono ${visual.label9 ?? ""}`}
                style={{ color: changed ? "var(--success)" : "var(--fg-muted)" }}
              >
                {String(m.b)}
              </span>
              <span className={visual.caption6}>{m.note}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
