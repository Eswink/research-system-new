import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import visual from "./ProjectsGridView.module.css";
import { ProjectStatusBadge } from "./ProjectStatusBadge";

/** Reference: screens/Projects.jsx; EXAMPLE ONLY. */
export const ProjectsGridView = ({ projects, onOpen, onContextMenu }: E.ProjectsViewProps) => {
  const { t } = useI18n();
  return (
    <div className={visual.grid}>
      {projects.map((p) => (
        <div
          key={p.id}
          onClick={() => {
            onOpen(p);
          }}
          onContextMenu={(e) => {
            onContextMenu(e, p);
          }}
          className={`panel ${visual.panel ?? ""}`}
        >
          <div className={visual.row}>
            <div className={visual.surface}>
              <div className={visual.label}>{p.name}</div>
              <div className={`mono ${visual.caption ?? ""}`}>{p.slug}</div>
            </div>
            <ProjectStatusBadge status={p.status} />
          </div>
          <div className={visual.row2}>
            {p.tags.slice(0, 4).map((t) => (
              <span key={t} className={`chip ${visual.caption2 ?? ""}`}>
                {t}
              </span>
            ))}
          </div>
          <ProjectsGridViewSection {...{ t, p }} />
        </div>
      ))}
    </div>
  );
};

interface ProjectsGridViewSectionProps {
  t: (key: string, fallback?: string) => string;
  p: E.Project;
}

function ProjectsGridViewSection({ t, p }: ProjectsGridViewSectionProps) {
  return (
    <div className={visual.grid2}>
      <div>
        <div className={visual.caption3}>{t("proj.card.runs")}</div>
        <div className={visual.label2}>{p.runs}</div>
      </div>
      <div>
        <div className={visual.caption4}>{t("proj.card.health")}</div>
        <div
          className={visual.label3}
          style={{
            color:
              p.health == null
                ? "var(--fg-faint)"
                : p.health >= 80
                  ? "var(--success)"
                  : p.health >= 50
                    ? "var(--warn)"
                    : "var(--danger)",
          }}
        >
          {p.health ?? "—"}
        </div>
      </div>
      <div>
        <div className={visual.caption5}>{t("proj.card.burn")}</div>
        <div className={visual.label4}>{Math.round((p.spent_minor / p.budget_minor) * 100)}%</div>
      </div>
    </div>
  );
}
