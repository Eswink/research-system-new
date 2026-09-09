import type * as R from "react";
import type * as E from "../../exampleTypes";
import { Icon } from "../Icon";

interface ProjectsActionProps {
  setProjectsLocal: R.Dispatch<R.SetStateAction<E.Project[]>>;
  drawer: { mode: "view" | "edit"; project: E.Project };
  setDrawer: R.Dispatch<R.SetStateAction<E.ProjectDrawer | null>>;
  t: (key: string, fallback?: string) => string;
}

export function ProjectsAction({ setProjectsLocal, drawer, setDrawer, t }: ProjectsActionProps) {
  return (
    <button
      className="btn ghost"
      onClick={() => {
        setProjectsLocal((prev) => [
          {
            ...drawer.project,
            id: `proj_dup_${crypto.randomUUID()}`,
            name: drawer.project.name + " (copy)",
            status: "DRAFT",
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          ...prev,
        ]);
        setDrawer(null);
      }}
    >
      <Icon name="fork" size={11} /> {t("act.duplicate")}
    </button>
  );
}
