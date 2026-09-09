import { type Dispatch, type SetStateAction } from "react";
import visual from "../DryRunScreen.module.css";
import { Icon } from "../Icon";
import { ZoneHeader } from "../ZoneHeader";
import type { ExamplePreflight } from "../preflightModel";
import { DryRunApprovals } from "./DryRunApprovals";
import { DryRunBudgetProj } from "./DryRunBudgetProj";
import { DryRunFindings3 } from "./DryRunFindings3";
import { DryRunResolved } from "./DryRunResolved";

interface DryRunFindings2Props {
  t: (key: string, fallback?: string) => string;
  preflight: ExamplePreflight;
  errorCount: number;
  warnCount: number;
  infoCount: number;
  selectedFinding: number;
  setSelectedFinding: Dispatch<SetStateAction<number>>;
}

export function DryRunFindings2({
  t,
  preflight,
  errorCount,
  warnCount,
  infoCount,
  selectedFinding,
  setSelectedFinding,
}: DryRunFindings2Props) {
  return (
    <div className={visual.column3}>
      {/* Zone: Findings */}
      <DryRunFindings3
        {...{ t, preflight, errorCount, warnCount, infoCount, selectedFinding, setSelectedFinding }}
      />

      {/* Zone: Resolved Plan (role_counts investment) */}
      <DryRunResolved {...{ t }} />

      {/* Zone: Budget */}
      <DryRunBudgetProj {...{ t, preflight }} />

      {/* Zone: Approvals (planned) */}
      <DryRunApprovals {...{ t }} />

      {/* Zone: Risks */}
      <section className="panel">
        <ZoneHeader
          icon="warn-tri"
          title={t("dr.risks")}
          count={preflight.unresolved_risks.length}
        />
        <div className={visual.surface13}>
          {preflight.unresolved_risks.length === 0 ? (
            <span className={visual.label9}>{t("dr.risksNone")}</span>
          ) : (
            preflight.unresolved_risks.map((r, i) => (
              <div key={i} className={visual.row8}>
                <Icon name="warn-tri" size={11} className={visual.surface14} /> {r}
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}
