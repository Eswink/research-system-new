import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../CompareScreen.module.css";
import { Icon } from "../Icon";
import { CompareSection6 } from "./CompareSection6";

interface CompareSection3Props {
  t: (key: string, fallback?: string) => string;
  manifestFields: (
    | { field: string; a: string; b: string; note: string }
    | { field: string; a: number; b: number; note: string }
  )[];
  visibleManifest: (
    | { field: string; a: string; b: string; note: string }
    | { field: string; a: number; b: number; note: string }
  )[];
  base: FixtureTypes.Run | undefined;
  selectedRuns: FixtureTypes.Run[];
}

export function CompareSection3({
  t,
  manifestFields,
  visibleManifest,
  base,
  selectedRuns,
}: CompareSection3Props) {
  return (
    <div className={visual.grid2}>
      <CompareSection6 {...{ t, manifestFields, visibleManifest }} />

      <div className={`panel ${visual.panel3 ?? ""}`}>
        <div className={visual.caption3}>{t("cmp.verdict")}</div>
        <div className={visual.label7}>
          {t("cmp.verdictLine1")}: <span className={visual.surface9}>A ({base?.label})</span>{" "}
          {t("cmp.verdictLine2")}
        </div>
        <div className={visual.grid3}>
          {selectedRuns.map((r, i) => (
            <div
              key={r.id}
              className={visual.surface10}
              style={{
                borderLeft: `2px solid ${String(
                  ["var(--accent)", "var(--warn)", "var(--success)", "var(--unknown)"][i],
                )}`,
              }}
            >
              <div className={visual.caption4}>{String.fromCharCode(65 + i)}</div>
              <div className={visual.label8}>{r.label}</div>
              <div className={visual.caption5}>
                ${(r.spent_minor / 1e6).toFixed(2)}M · {r.claims_new} claims · {r.tasks_done}/
                {r.tasks_total}
              </div>
            </div>
          ))}
        </div>
        <div className={visual.row7}>
          <button className={`btn sm ${visual.action2 ?? ""}`}>
            <Icon name="fork" size={10} /> {t("cmp.forkFromA")}
          </button>
          <button className={`btn sm primary ${visual.action3 ?? ""}`}>
            <Icon name="external" size={10} /> {t("cmp.openReport")}
          </button>
        </div>
      </div>
    </div>
  );
}
