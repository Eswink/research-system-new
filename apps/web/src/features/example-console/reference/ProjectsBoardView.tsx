import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import visual from "./ProjectsBoardView.module.css";

/** Reference: screens/Projects.jsx; EXAMPLE ONLY. */
export const ProjectsBoardView = ({ projects, onOpen, onContextMenu }: E.ProjectsViewProps) => {
  const cols = ["DRAFT", "RUNNING", "PAUSED", "SUCCEEDED", "FAILED", "ARCHIVED"];
  return (
    <div className={visual.grid}>
      {cols.map((col) => {
        const items = projects.filter((p) => p.status === col);
        return (
          <div key={col} className={`panel ${visual.panel ?? ""}`}>
            <div className={visual.row}>
              {col.toLowerCase()} <span className={visual.surface}>{items.length}</span>
            </div>
            {items.map((p) => (
              <div
                key={p.id}
                onClick={() => {
                  onOpen(p);
                }}
                onContextMenu={(e) => {
                  onContextMenu(e, p);
                }}
                className={visual.surface2}
              >
                <div className={visual.label}>{p.name}</div>
                <ProjectsBoardViewSection {...{ p }} />
              </div>
            ))}
            {items.length === 0 && (
              <div className={visual.caption}>
                {typeof useI18n === "function" ? useI18n().t("proj.boardEmpty") : "empty"}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

interface ProjectsBoardViewSectionProps {
  p: E.Project;
}

function ProjectsBoardViewSection({ p }: ProjectsBoardViewSectionProps) {
  return (
    <div className={visual.row2}>
      <span>{p.runs} runs</span>
      <span
        style={{
          color:
            (p.health ?? -1) >= 80
              ? "var(--success)"
              : (p.health ?? -1) >= 50
                ? "var(--warn)"
                : p.health != null
                  ? "var(--danger)"
                  : "var(--fg-faint)",
        }}
      >
        {p.health != null ? String(p.health) : "—"}
      </span>
    </div>
  );
}
