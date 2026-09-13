import { api } from "../api/client";
import { getActiveProjectId, setActiveProjectId } from "../api/activeProject";
import { EXAMPLE_WORKSPACES } from "../features/example-console/exampleChrome";
import { WorkspaceSwitcher } from "../features/example-console/reference/WorkspaceSwitcher";
import { useResource } from "../hooks/useResource";
import { useI18n } from "../i18n/useI18n";
import { usePresentation } from "../navigation/usePresentation";
import styles from "./WorkspaceIdentity.module.css";

export function WorkspaceIdentity() {
  const { source } = usePresentation();
  const { language } = useI18n();
  return (
    <div className={styles.identity}>
      {source === "example" ? (
        <WorkspaceSwitcher workspaces={EXAMPLE_WORKSPACES} />
      ) : (
        <ProjectSwitcher zh={language === "zh"} />
      )}
    </div>
  );
}

/** Live 项目切换器（PLAN-041 WP-C）：注册表真实数据；读失败回落中性 chip。 */
function ProjectSwitcher({ zh }: { zh: boolean }) {
  const projects = useResource("projects", () => api.listProjects());
  const activeId = getActiveProjectId();
  const items = projects.data ?? [];
  if (items.length === 0) {
    return <span className="chip">{zh ? "个人工作区" : "Personal workspace"}</span>;
  }
  return (
    <label className={styles.identity}>
      <span className="visually-hidden">{zh ? "切换项目" : "Switch project"}</span>
      <select
        className="input sm"
        data-testid="project-switcher"
        value={activeId}
        onChange={(event) => {
          setActiveProjectId(event.target.value);
          globalThis.location.reload();
        }}
      >
        {items.map((project) => (
          <option key={project.id} value={project.id}>
            {project.name}
            {project.status === "ARCHIVED" ? (zh ? "（已归档）" : " (archived)") : ""}
          </option>
        ))}
      </select>
    </label>
  );
}
