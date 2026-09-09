import { type Dispatch, type SetStateAction } from "react";
import visual from "../DryRunScreen.module.css";
import { FindingRow } from "../FindingRow";
import { Icon } from "../Icon";
import type { ExamplePreflight } from "../preflightModel";
import { DryRunFindings4 } from "./DryRunFindings4";

interface DryRunFindings3Props {
  t: (key: string, fallback?: string) => string;
  preflight: ExamplePreflight;
  errorCount: number;
  warnCount: number;
  infoCount: number;
  selectedFinding: number;
  setSelectedFinding: Dispatch<SetStateAction<number>>;
}

export function DryRunFindings3({
  t,
  preflight,
  errorCount,
  warnCount,
  infoCount,
  selectedFinding,
  setSelectedFinding,
}: DryRunFindings3Props) {
  return (
    <section className="panel">
      <DryRunFindings4 {...{ t, preflight, errorCount, warnCount, infoCount }} />
      {preflight.findings.length === 0 ? (
        <div className={visual.surface5}>
          <Icon name="check" size={14} className={visual.surface6} />
          <div className={visual.surface7}>{t("dr.noFindings")}</div>
        </div>
      ) : (
        preflight.findings.map((f, i) => (
          <FindingRow
            key={i}
            finding={f}
            selected={i === selectedFinding}
            onSelect={() => {
              setSelectedFinding(i);
            }}
          />
        ))
      )}
    </section>
  );
}
