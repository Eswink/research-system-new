import type * as R from "react";
import type * as E from "../../exampleTypes";
import { Icon } from "../Icon";
import visual from "../ProjectsScreen.module.css";
import { ProjectsAction } from "./ProjectsAction";

interface ProjectsContentProps {
  setDrawer: R.Dispatch<R.SetStateAction<E.ProjectDrawer | null>>;
  drawer: { mode: "view" | "edit"; project: E.Project };
  t: (key: string, fallback?: string) => string;
  setProjectsLocal: R.Dispatch<R.SetStateAction<E.Project[]>>;
  setConfirmDelete: R.Dispatch<R.SetStateAction<E.Project | null>>;
}

export function ProjectsContent({
  setDrawer,
  drawer,
  t,
  setProjectsLocal,
  setConfirmDelete,
}: ProjectsContentProps) {
  return (
    <>
      <button
        className="btn"
        onClick={() => {
          setDrawer({ mode: "edit", project: drawer.project });
        }}
      >
        <Icon name="copy" size={11} /> {t("act.edit")}
      </button>
      {
        <ProjectsAction
          {...{
            setProjectsLocal: setProjectsLocal,
            drawer: drawer,
            setDrawer: setDrawer,
            t: t,
          }}
        />
      }
      <button
        className={`btn ghost ${visual.action2 ?? ""}`}
        onClick={() => {
          setConfirmDelete(drawer.project);
          setDrawer(null);
        }}
      >
        <Icon name="x" size={11} /> {t("act.delete")}
      </button>
    </>
  );
}
