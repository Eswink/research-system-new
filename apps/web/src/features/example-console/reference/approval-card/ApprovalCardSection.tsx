import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../ApprovalCard.module.css";
import { ApprovalCardSection2 } from "./ApprovalCardSection2";
import { ApprovalCardSection3 } from "./ApprovalCardSection3";

interface ApprovalCardSectionProps {
  onSelect: () => void;
  selected: boolean;
  approval: FixtureTypes.Approval;
  riskTone: string;
  t: (key: string, fallback?: string) => string;
}

export function ApprovalCardSection({
  onSelect,
  selected,
  approval,
  riskTone,
  t,
}: ApprovalCardSectionProps) {
  return (
    <div
      onClick={onSelect}
      className={visual.surface}
      style={{
        background: selected ? "var(--bg-hover)" : "var(--bg-raised)",
        border: `1px solid ${
          selected
            ? "var(--accent)"
            : approval.risk === "high"
              ? "var(--danger-line)"
              : "var(--border)"
        }`,
        borderLeft: `3px solid var(--${
          approval.risk === "high" ? "danger" : approval.risk === "medium" ? "warn" : "fg-muted"
        })`,
      }}
    >
      <ApprovalCardSection3 {...{ approval, riskTone }} />
      <div className={visual.label}>
        <span className={`mono ${visual.surface2 ?? ""}`}>{approval.action.verb}</span> ·{" "}
        {approval.action.reason}
      </div>
      <ApprovalCardSection2 {...{ approval }} />
      <div className={visual.row2}>
        {approval.consequence.produces_manifest_revision && (
          <span className={visual.surface3}>{t("ap.badgeMR")}</span>
        )}
        {approval.consequence.external_side_effects && (
          <span className={visual.surface4}>{t("ap.badgeExt")}</span>
        )}
        <span className={visual.surface5}>
          {t("ap.affectsTask")} {approval.consequence.affected_tasks} {t("lbl.tasks").toLowerCase()}
          {approval.consequence.affected_tasks !== 1 ? "s" : ""}
        </span>
      </div>
    </div>
  );
}
