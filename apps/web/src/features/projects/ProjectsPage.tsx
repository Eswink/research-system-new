import { useState, type FormEvent } from "react";

import { api } from "../../api/client";
import { getActiveProjectId, setActiveProjectId } from "../../api/activeProject";
import type { ProjectDto } from "../../api/types";
import { Button } from "../../components/Button";
import { Chip } from "../../components/Chip";
import { ResourceBoundary } from "../../components/ResourceBoundary";
import { EmptyState, ErrorState } from "../../components/States";
import { useResource } from "../../hooks/useResource";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";
import { PageHeader } from "../shared/PageHeader";

/** 项目集（PLAN-041 WP-C）：真实注册表视图（列表/创建/归档/切换活动项目）。 */
export function ProjectsPage() {
  const { t } = useI18n();
  const projects = useResource("projects", () => api.listProjects());
  return (
    <section className={styles.page} data-testid="projects-page">
      <ProjectsPageHeader
        title={t("page.portfolio.projects")}
        description={t("projects.hint")}
        onCreate={projects.reload}
      />
      <ResourceBoundary state={projects}>
        {projects.data !== null && (
          <ProjectRows projects={projects.data} onChanged={projects.reload} />
        )}
      </ResourceBoundary>
      {projects.error !== null && <ErrorState message={projects.error} />}
    </section>
  );
}

function ProjectsPageHeader({
  title,
  description,
  onCreate,
}: {
  title: string;
  description: string;
  onCreate: () => void;
}) {
  return (
    <PageHeader
      title={title}
      kicker="PORTFOLIO / PROJECTS"
      description={description}
      actions={<CreateProjectForm onCreated={onCreate} />}
    />
  );
}

function CreateProjectForm({ onCreated }: { onCreated: () => void }) {
  const { t } = useI18n();
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const submit = (event: FormEvent): void => {
    event.preventDefault();
    const trimmed = name.trim();
    if (trimmed === "" || busy) return;
    setBusy(true);
    setError(null);
    void api
      .createProject(trimmed)
      .then(() => {
        setName("");
        onCreated();
      })
      .catch((reason: unknown) => {
        setError(reason instanceof Error ? reason.message : String(reason));
      })
      .finally(() => {
        setBusy(false);
      });
  };
  return (
    <form className={styles.toolbar} onSubmit={submit}>
      <input
        className="input"
        value={name}
        aria-label={t("projects.name")}
        placeholder={t("projects.create.placeholder")}
        disabled={busy}
        onChange={(event) => {
          setName(event.target.value);
        }}
      />
      <Button type="submit" variant="primary" disabled={busy || name.trim() === ""}>
        {busy ? t("projects.creating") : t("projects.create")}
      </Button>
      {error !== null && <ErrorState message={error} />}
    </form>
  );
}

function ProjectRows({
  projects,
  onChanged,
}: {
  projects: ProjectDto[];
  onChanged: () => void;
}) {
  const { t } = useI18n();
  const activeId = getActiveProjectId();
  if (projects.length === 0) {
    return <EmptyState message={t("projects.empty")} />;
  }
  return (
    <ul className={styles.list} data-testid="projects-list">
      {projects.map((project) => (
        <ProjectRow
          key={project.id}
          project={project}
          isActive={project.id === activeId}
          onChanged={onChanged}
        />
      ))}
    </ul>
  );
}

function ProjectRow({
  project,
  isActive,
  onChanged,
}: {
  project: ProjectDto;
  isActive: boolean;
  onChanged: () => void;
}) {
  const { t } = useI18n();
  const [busy, setBusy] = useState(false);
  const active = project.status === "ACTIVE";
  const toggleArchive = (): void => {
    setBusy(true);
    void api
      .updateProject(project.id, { status: active ? "ARCHIVED" : "ACTIVE" })
      .then(onChanged)
      .finally(() => {
        setBusy(false);
      });
  };
  return (
    <li data-testid={`project-row-${project.id}`}>
      <div className={styles.listButton}>
        <strong>{project.name}</strong>{" "}
        {isActive && <Chip tone="accent">{t("projects.active")}</Chip>}{" "}
        <Chip tone={active ? "success" : "neutral"}>
          {active ? t("projects.status.active") : t("projects.status.archived")}
        </Chip>{" "}
        <span className="mono">{project.id}</span>
      </div>
      <div className={styles.toolbar}>
        {!isActive && <ProjectSwitchAction projectId={project.id} busy={busy} />}
        <button
          type="button"
          className="btn sm"
          disabled={busy}
          data-testid={`project-archive-${project.id}`}
          onClick={toggleArchive}
        >
          {active ? t("projects.archive") : t("projects.restore")}
        </button>
      </div>
    </li>
  );
}

function ProjectSwitchAction({ projectId, busy }: { projectId: string; busy: boolean }) {
  const { t } = useI18n();
  return (
    <button
      type="button"
      className="btn sm"
      disabled={busy}
      data-testid={`project-switch-${projectId}`}
      onClick={() => {
        setActiveProjectId(projectId);
        globalThis.location.reload();
      }}
    >
      {t("projects.set-active")}
    </button>
  );
}
