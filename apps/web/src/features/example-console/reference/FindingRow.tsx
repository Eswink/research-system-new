import type * as E from "../exampleTypes";
import visual from "./FindingRow.module.css";
import { Icon } from "./Icon";

/** Reference: screens/DryRun.jsx; EXAMPLE ONLY. */
export const FindingRow = ({
  finding,
  selected,
  onSelect,
}: {
  finding: E.Finding;
  selected: boolean;
  onSelect: () => void;
}) => {
  const sev = finding.severity;
  const color =
    sev === "error" ? "var(--danger)" : sev === "warning" ? "var(--warn)" : "var(--accent)";
  const icon = sev === "error" ? "x" : sev === "warning" ? "warn-tri" : "circle-o";
  return (
    <div
      onClick={onSelect}
      className={visual.grid}
      style={{ background: selected ? "var(--bg-hover)" : "transparent" }}
    >
      <Icon name={icon} size={12} className={visual.surface} style={{ color }} />
      <span className={`mono ${visual.label ?? ""}`}>{finding.code}</span>
      <div className={visual.label2}>{finding.message}</div>
      <button
        className="btn sm ghost"
        title="Jump to subject"
        onClick={(e) => {
          e.stopPropagation();
        }}
      >
        <Icon name="external" size={10} /> {finding.subject_ref.kind}:
        {finding.subject_ref.id.slice(0, 12)}…
      </button>
    </div>
  );
};
