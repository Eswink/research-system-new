import visual from "../DataHealthScreen.module.css";
import { Sparkline } from "../Sparkline";

interface DataHealthSection3Props {
  t: (key: string, fallback?: string) => string;
  selected: {
    id: string;
    dataset: string;
    rows: number;
    drift: number;
    freshness_d: number;
    pii_hits: number;
    label_skew: number;
    schema_ok: boolean;
  };
}

export function DataHealthSection3({ t, selected }: DataHealthSection3Props) {
  return (
    <div>
      <div className={visual.caption2}>{t("dh.driftTrend")} · 30d</div>
      <div className={visual.surface6}>
        <div className={visual.row2}>
          <span
            className={visual.label9}
            style={{ color: selected.drift > 0.15 ? "var(--warn)" : "var(--fg)" }}
          >
            {(selected.drift * 100).toFixed(1)}%
          </span>
          <span className={visual.label10}>PSI</span>
          <span className={`mono ${visual.caption3 ?? ""}`}>threshold: 15%</span>
        </div>
        <Sparkline
          data={Array.from({ length: 30 }, (_, i) =>
            Math.max(0.01, selected.drift * (0.6 + Math.sin(i * 0.5) * 0.4 + i / 60)),
          )}
          width={340}
          height={44}
          stroke={selected.drift > 0.15 ? "var(--warn)" : "var(--accent)"}
          fill={selected.drift > 0.15 ? "var(--warn-dim)" : "var(--accent-dim)"}
        />
      </div>
    </div>
  );
}
