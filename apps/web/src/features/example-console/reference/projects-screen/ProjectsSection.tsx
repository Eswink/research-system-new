import type * as R from "react";
import visual from "../ProjectsScreen.module.css";

interface ProjectsSectionProps {
  t: (key: string, fallback?: string) => string;
  setStatusFilter: R.Dispatch<R.SetStateAction<string>>;
  statusFilter: string;
  counts: Record<string, number>;
}

export function ProjectsSection({
  t,
  setStatusFilter,
  statusFilter,
  counts,
}: ProjectsSectionProps) {
  return (
    <div className={visual.row}>
      {(
        [
          ["all", t("lbl.all")],
          ["RUNNING", t("proj.filterRunning")],
          ["PAUSED", t("proj.filterPaused")],
          ["DRAFT", t("proj.filterDraft")],
          ["SUCCEEDED", t("proj.filterSucceeded")],
          ["FAILED", t("proj.filterFailed")],
          ["ARCHIVED", t("proj.filterArchived")],
        ] as const
      ).map(([s, l]) => (
        <button
          key={s}
          onClick={() => {
            setStatusFilter(s);
          }}
          className={`btn sm ghost ${visual.action ?? ""}`}
          style={{
            background: statusFilter === s ? "var(--bg-hover)" : "transparent",
            color: statusFilter === s ? "var(--fg)" : "var(--fg-muted)",
            fontWeight: statusFilter === s ? 500 : 400,
          }}
        >
          {l} <span className={visual.caption}>{counts[s] ?? 0}</span>
        </button>
      ))}
    </div>
  );
}
