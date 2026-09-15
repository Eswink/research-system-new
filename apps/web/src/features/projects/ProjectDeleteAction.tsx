import { DEFAULT_PROJECT_ID } from "../../api/activeProject";
import type { ProjectDto } from "../../api/types";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import { ErrorState } from "../../components/States";
import { useI18n } from "../../i18n/useI18n";
import styles from "../shared/LivePage.module.css";
import { useProjectDeletion } from "./useProjectDeletion";

/**
 * 项目删除动作（EC-06/PLAN-061 接线 DELETE /projects/{id}）。
 *
 * 默认项目是合成基线（删了也还在），不给删除入口；引用中的项目由后端 409 拒绝
 * 并回传引用清单，客户端只呈现该文案。状态机见 useProjectDeletion。
 */
export function ProjectDeleteAction({
  project,
  onDeleted,
}: {
  project: ProjectDto;
  onDeleted: () => void;
}) {
  const { t } = useI18n();
  const { confirming, setConfirming, busy, error, runDelete } = useProjectDeletion(
    project.id,
    onDeleted,
  );
  const reserved = project.id === DEFAULT_PROJECT_ID;
  return (
    <>
      <button
        type="button"
        className="btn sm danger"
        disabled={busy || reserved}
        title={reserved ? t("projects.delete.reserved") : t("projects.delete")}
        data-testid={`project-delete-${project.id}`}
        onClick={() => {
          setConfirming(true);
        }}
      >
        {busy ? t("projects.deleting") : t("projects.delete")}
      </button>
      {error !== null && <ErrorState message={error} />}
      <ProjectDeleteConfirm
        open={confirming}
        busy={busy}
        project={project}
        onConfirm={runDelete}
        onCancel={() => {
          setConfirming(false);
        }}
      />
    </>
  );
}

function ProjectDeleteConfirm({
  open,
  busy,
  project,
  onConfirm,
  onCancel,
}: {
  open: boolean;
  busy: boolean;
  project: ProjectDto;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const { t } = useI18n();
  return (
    <ConfirmDialog
      open={open}
      danger
      title={t("projects.delete.title")}
      consequence={
        <p className={styles.notice}>
          {project.name} · <span className="mono">{project.id}</span> ·{" "}
          {t("projects.delete.consequence")}
        </p>
      }
      busy={busy}
      confirmLabel={t("projects.delete.confirm")}
      cancelLabel={t("projects.delete.cancel")}
      onConfirm={onConfirm}
      onCancel={onCancel}
    />
  );
}
