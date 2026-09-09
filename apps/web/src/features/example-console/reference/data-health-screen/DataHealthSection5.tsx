import visual from "../DataHealthScreen.module.css";

interface DataHealthSection5Props {
  t: (key: string, fallback?: string) => string;
}

export function DataHealthSection5({ t }: DataHealthSection5Props) {
  return (
    <div>
      <div className={visual.caption4}>{t("dh.labelDist")}</div>
      <div className={visual.column3}>
        {[
          { name: "class_a", pct: 0.42 },
          { name: "class_b", pct: 0.31 },
          { name: "class_c", pct: 0.18 },
          { name: "class_d", pct: 0.09 },
        ].map((c) => (
          <div key={c.name} className={visual.grid3}>
            <span className={`mono ${visual.caption5 ?? ""}`}>{c.name}</span>
            <div className={visual.indicator}>
              <div className={visual.indicator2} style={{ width: `${String(c.pct * 100)}%` }} />
            </div>
            <span className={`mono ${visual.caption6 ?? ""}`}>{(c.pct * 100).toFixed(0)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
