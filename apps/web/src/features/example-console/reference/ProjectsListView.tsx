import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { Icon } from "./Icon";
import visual from "./ProjectsListView.module.css";
import { ProjectStatusBadge } from "./ProjectStatusBadge";

/** Reference: screens/Projects.jsx; EXAMPLE ONLY. */
export const ProjectsListView = ({ projects, onOpen, onContextMenu }: E.ProjectsViewProps) => {
  const { t } = useI18n();
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={`row head ${visual.surface ?? ""}`}>
        <span></span>
        <span>{t("proj.colProject")}</span>
        <span>{t("lbl.status")}</span>
        <span>{t("proj.colHealth")}</span>
        <span>{t("proj.colBudget")}</span>
        <span>{t("proj.colRuns")}</span>
        <span>{t("lbl.updated")}</span>
        <span>{t("lbl.owner")}</span>
      </div>
      {projects.map((p) => (
        <div
          key={p.id}
          className={`row ${visual.surface2 ?? ""}`}
          onContextMenu={(e) => {
            onContextMenu(e, p);
          }}
          onClick={() => {
            onOpen(p);
          }}
        >
          <span style={{ color: p.favorited ? "var(--warn)" : "var(--fg-faint)" }}>
            <Icon name={p.favorited ? "diamond" : "circle-o"} size={11} />
          </span>
          <ProjectsListViewSection {...{ p }} />
          <span>
            <ProjectStatusBadge status={p.status} />
          </span>
          <ProjectsListViewLabel {...{ p }} />
          <span className={visual.label3}>
            ${(p.spent_minor / 100000).toFixed(0)} / ${(p.budget_minor / 100000).toFixed(0)}
          </span>
          <span className={visual.label4}>{p.runs}</span>
          <span className={visual.label5}>
            {new Date(p.updated_at).toLocaleDateString("en-CA")}
          </span>
          <span className={visual.label6}>{p.owner.split("@")[0]}</span>
        </div>
      ))}
    </div>
  );
};

interface ProjectsListViewLabelProps {
  p: E.Project;
}

interface ProjectsListViewSectionProps {
  p: E.Project;
}

function ProjectsListViewSection({ p }: ProjectsListViewSectionProps) {
  return (
    <div className={`row-cell-wrap ${visual.surface3 ?? ""}`}>
      <div className={visual.label}>{p.name}</div>
      <div className={visual.row}>
        <span className={visual.surface4}>{p.slug}</span>
        {p.tags.slice(0, 2).map((tg) => (
          <span key={tg} className={`chip ${visual.caption ?? ""}`}>
            {tg}
          </span>
        ))}
        {p.tags.length > 2 && <span className={visual.caption2}>+{p.tags.length - 2}</span>}
      </div>
    </div>
  );
}

function ProjectsListViewLabel({ p }: ProjectsListViewLabelProps) {
  return (
    <span>
      {p.health == null ? (
        <span className="empty-mark">—</span>
      ) : (
        <div className={visual.row2}>
          <div className={visual.indicator}>
            <div
              className={visual.surface5}
              style={{
                width: `${String(p.health)}%`,
                background:
                  p.health >= 80
                    ? "var(--success)"
                    : p.health >= 50
                      ? "var(--warn)"
                      : "var(--danger)",
              }}
            />
          </div>
          <span
            className={visual.label2}
            style={{
              color:
                p.health >= 80
                  ? "var(--success)"
                  : p.health >= 50
                    ? "var(--warn)"
                    : "var(--danger)",
            }}
          >
            {p.health}
          </span>
        </div>
      )}
    </span>
  );
}
