import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../ApprovalsScreen.module.css";
import { DigestText } from "../DigestText";
import { GateChip } from "../GateChip";

interface ApprovalsSection2Props {
  selected: FixtureTypes.Approval;
  t: (key: string, fallback?: string) => string;
}

export function ApprovalsSection2({ selected, t }: ApprovalsSection2Props) {
  return (
    <div className={visual.row3}>
      <GateChip type={selected.policy_source} />
      <span
        className={`chip`}
        style={{
          color:
            selected.risk === "high"
              ? "var(--danger)"
              : selected.risk === "medium"
                ? "var(--warn)"
                : "var(--fg-muted)",
          borderColor:
            selected.risk === "high"
              ? "var(--danger-line)"
              : selected.risk === "medium"
                ? "var(--warn-line)"
                : "var(--border)",
        }}
      >
        {t("ap.risk")} {selected.risk}
      </span>
      <DigestText value={selected.id} length={14} prefix={false} />
      <span className={`chip ${visual.surface5 ?? ""}`}>
        v{selected.version} · {t("ap.ifMatch")}
      </span>
    </div>
  );
}
