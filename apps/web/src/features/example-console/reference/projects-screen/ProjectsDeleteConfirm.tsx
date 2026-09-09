import type * as R from "react";
import type * as E from "../../exampleTypes";
import { Icon } from "../Icon";
import { Modal } from "../Modal";
import visual from "../ProjectsScreen.module.css";
import { ProjectsContent3 } from "./ProjectsContent3";

interface ProjectsDeleteConfirmProps {
  confirmDelete: E.Project | null;
  setConfirmDelete: R.Dispatch<R.SetStateAction<E.Project | null>>;
  t: (key: string, fallback?: string) => string;
  setProjectsLocal: R.Dispatch<R.SetStateAction<E.Project[]>>;
}

export function ProjectsDeleteConfirm({
  confirmDelete,
  setConfirmDelete,
  t,
  setProjectsLocal,
}: ProjectsDeleteConfirmProps) {
  return (
    <Modal
      open={!!confirmDelete}
      onClose={() => {
        setConfirmDelete(null);
      }}
      title={t("proj.deleteConfirm")}
      footer={
        <ProjectsContent3
          {...{
            setConfirmDelete: setConfirmDelete,
            t: t,
            setProjectsLocal: setProjectsLocal,
            confirmDelete: confirmDelete,
          }}
        />
      }
    >
      <div className={visual.label}>
        {t("proj.deleteMsg")} <strong className={visual.surface2}>{confirmDelete?.name}</strong>
        {". "}
        {t("proj.deleteMsg2").replace("{n}", String(confirmDelete?.runs ?? 0))}
      </div>
      <div className={visual.row2}>
        <Icon name="warn-tri" size={12} />{" "}
        <div>
          {t("proj.archiveHint")} <strong>{t("act.archive").toLowerCase()}</strong>{" "}
          {t("proj.archiveHint2")}
        </div>
      </div>
    </Modal>
  );
}
