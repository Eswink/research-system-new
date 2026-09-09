import * as React from "react";
import visual from "../ExperimentMatrix.module.css";

interface ExperimentMatrixSection3Props {
  temps: number[];
  models: string[];
  status: (i: number, j: number, k: number) => "RUNNING" | "SUCCEEDED" | "FAILED" | "PENDING";
  li: number;
  lang: string;
  color: (s: string) => "var(--success)" | "var(--accent)" | "var(--danger)" | "var(--bg-sunken)";
}

export function ExperimentMatrixSection3({
  temps,
  models,
  status,
  li,
  lang,
  color,
}: ExperimentMatrixSection3Props) {
  return (
    <div
      className={visual.grid}
      style={{ gridTemplateColumns: `100px repeat(${String(temps.length)}, 1fr)` }}
    >
      <div />
      {temps.map((t) => (
        <div key={t} className={visual.caption2}>
          temp={t}
        </div>
      ))}
      {models.map((m, mi) => (
        <React.Fragment key={m}>
          <div className={visual.caption3}>{m}</div>
          {temps.map((t, ti) => {
            const s = status(li, mi, ti);
            return (
              <div
                key={ti}
                title={`${lang} × ${m} × temp=${String(t)} · ${s}`}
                className={visual.row}
                style={{
                  background: color(s),
                  opacity: s === "PENDING" ? 0.5 : 1,
                  color: s === "PENDING" ? "var(--fg-faint)" : "#fff",
                  border: s === "PENDING" ? "1px dashed var(--border-strong)" : "none",
                }}
              >
                {s === "SUCCEEDED" && "✓"}
                {s === "RUNNING" && "…"}
                {s === "FAILED" && "✕"}
                {s === "PENDING" && "○"}
              </div>
            );
          })}
        </React.Fragment>
      ))}
    </div>
  );
}
