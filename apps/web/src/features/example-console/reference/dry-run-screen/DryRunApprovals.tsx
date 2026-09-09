import visual from "../DryRunScreen.module.css";
import { GateChip } from "../GateChip";
import { ZoneHeader } from "../ZoneHeader";

interface DryRunApprovalsProps {
  t: (key: string, fallback?: string) => string;
}

export function DryRunApprovals({ t }: DryRunApprovalsProps) {
  return (
    <section className="panel">
      <ZoneHeader
        icon="shield"
        title={t("dr.approvals")}
        count={4}
        extra={<span className={visual.label8}>{t("dr.approvalsHint")}</span>}
      />
      <div className={visual.column4}>
        {[
          { gate: "BUDGET_GATE", trigger: "at 60% of cap", risk: "medium" },
          { gate: "QUALITY_GATE", trigger: "after each language subset (×7)", risk: "low" },
          { gate: "PUBLISH_GATE", trigger: "before deliverable finalized", risk: "high" },
          { gate: "SECURITY_GATE", trigger: "any external artifact publish", risk: "high" },
        ].map((g, i) => (
          <div key={i} className={visual.row7}>
            <GateChip type={g.gate} />
            <span className={visual.surface12}>{g.trigger}</span>
            <span
              className={visual.caption2}
              style={{
                color:
                  g.risk === "high"
                    ? "var(--danger)"
                    : g.risk === "medium"
                      ? "var(--warn)"
                      : "var(--fg-faint)",
              }}
            >
              risk: {g.risk}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
