import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { DigestText } from "./DigestText";
import { Icon } from "./Icon";
import { MetricCard } from "./MetricCard";
import visual from "./ProjectDetail.module.css";
import { ProjectStatusBadge } from "./ProjectStatusBadge";

/** Reference: screens/Projects.jsx; EXAMPLE ONLY. */
export const ProjectDetail = ({ project }: { project: E.Project }) => {
  const { t } = useI18n();
  return (
    <div className={visual.column}>
      <ProjectIdentity project={project} t={t} />

      <ProjectDetailCardRuns {...{ t, project }} />

      <ProjectTags project={project} t={t} />

      {(project.paused_reason ?? project.failure_reason) && (
        <div className={visual.row3}>
          <Icon name="warn-tri" size={12} />{" "}
          <div>{project.paused_reason ?? project.failure_reason}</div>
        </div>
      )}

      <div>
        <div className={visual.caption3}>{t("exp.meta").toUpperCase()}</div>
        <div className={visual.grid2}>
          <span className={visual.surface6}>owner</span>
          <span>{project.owner}</span>
          <span className={visual.surface7}>{t("lbl.created")}</span>
          <span>{new Date(project.created_at).toISOString().replace("T", " ").slice(0, 16)}</span>
          <span className={visual.surface8}>{t("lbl.updated").toLowerCase()}</span>
          <span>{new Date(project.updated_at).toISOString().replace("T", " ").slice(0, 16)}</span>
          <span className={visual.surface9}>{t("lbl.template")}</span>
          <span>{project.team_template}</span>
        </div>
      </div>
    </div>
  );
};

function ProjectIdentity({
  project,
  t,
}: {
  project: E.Project;
  t: ProjectDetailCardRunsProps["t"];
}) {
  return (
    <div className={visual.row}>
      <ProjectStatusBadge status={project.status} />
      <DigestText value={project.id} length={16} prefix={false} />
      <span className="chip">{project.team_template}</span>
      {project.favorited && (
        <span className={`chip ${visual.surface ?? ""}`}>
          <Icon name="diamond" size={9} /> {t("proj.card.pinned")}
        </span>
      )}
    </div>
  );
}

function ProjectTags({ project, t }: { project: E.Project; t: ProjectDetailCardRunsProps["t"] }) {
  return (
    <div>
      <div className={visual.caption2}>{t("lbl.tags")}</div>
      <div className={visual.row2}>
        {project.tags.map((tag) => (
          <span key={tag} className={`chip ${visual.surface5 ?? ""}`}>
            {tag}
          </span>
        ))}
      </div>
    </div>
  );
}

interface ProjectDetailCardRunsProps {
  t: (key: string, fallback?: string) => string;
  project: E.Project;
}

function ProjectDetailCardRuns({ t, project }: ProjectDetailCardRunsProps) {
  return (
    <div>
      <div className={visual.caption}>{t("proj.overview").toUpperCase()}</div>
      <ProjectDetailCardRuns2 {...{ t, project }} />
    </div>
  );
}

interface ProjectDetailCardRuns2Props {
  t: (key: string, fallback?: string) => string;
  project: E.Project;
}

function ProjectDetailCardRuns2({ t, project }: ProjectDetailCardRuns2Props) {
  return (
    <div className={visual.grid}>
      <MetricCard
        label={t("proj.card.runs")}
        value={project.runs}
        sub={
          <span>
            {project.active_agents} {t("proj.card.activeAgents")}
          </span>
        }
      />
      <MetricCard
        label={t("proj.card.health")}
        value={project.health ?? "—"}
        sub={<span>{t("proj.card.score")}</span>}
        bar={project.health != null ? project.health / 100 : 0}
        barColor={
          project.health == null
            ? "var(--fg-faint)"
            : project.health >= 80
              ? "var(--success)"
              : project.health >= 50
                ? "var(--warn)"
                : "var(--danger)"
        }
      />
      <MetricCard
        label={t("bg.totalSpent")}
        value={`$${(project.spent_minor / 100000).toFixed(2)}`}
        sub={
          <span>
            {t("proj.card.spentOf")}{" "}
            <span className="mono">${(project.budget_minor / 100000).toFixed(2)}</span> ·{" "}
            {Math.round((project.spent_minor / project.budget_minor) * 100)}%
          </span>
        }
        bar={project.spent_minor / project.budget_minor}
        barColor="var(--accent)"
      />
      <ProjectDetailClaims {...{ t, project }} />
    </div>
  );
}

interface ProjectDetailClaimsProps {
  t: (key: string, fallback?: string) => string;
  project: E.Project;
}

function ProjectDetailClaims({ t, project }: ProjectDetailClaimsProps) {
  return (
    <MetricCard
      label={t("gv.claims").toUpperCase()}
      value={
        project.claims.verified +
        project.claims.disputed +
        project.claims.proposed +
        project.claims.refuted
      }
      sub={
        <span>
          <span className={visual.surface2}>
            {project.claims.verified} {t("proj.status.verified")}
          </span>{" "}
          ·{" "}
          <span className={visual.surface3}>
            {project.claims.disputed} {t("proj.status.disputed")}
          </span>{" "}
          ·{" "}
          <span className={visual.surface4}>
            {project.claims.refuted} {t("proj.status.refuted")}
          </span>
        </span>
      }
    />
  );
}
