import type * as R from "react";
import type * as E from "../../exampleTypes";
import { Icon } from "../Icon";

interface ProjectsContent3Props {
  setConfirmDelete: R.Dispatch<R.SetStateAction<E.Project | null>>;
  t: (key: string, fallback?: string) => string;
  setProjectsLocal: R.Dispatch<R.SetStateAction<E.Project[]>>;
  confirmDelete: E.Project | null;
}

export function ProjectsContent3({
  setConfirmDelete,
  t,
  setProjectsLocal,
  confirmDelete,
}: ProjectsContent3Props) {
  return (
    <>
      <button
        className="btn ghost"
        onClick={() => {
          setConfirmDelete(null);
        }}
      >
        {t("act.cancel")}
      </button>
      <button
        className="btn danger"
        onClick={() => {
          setProjectsLocal((prev) => prev.filter((p) => p.id !== confirmDelete?.id));
          setConfirmDelete(null);
        }}
      >
        <Icon name="x" size={11} /> {t("act.deletePerm")}
      </button>
    </>
  );
}
