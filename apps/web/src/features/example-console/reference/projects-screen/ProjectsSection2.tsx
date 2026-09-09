import type * as R from "react";
import type * as E from "../../exampleTypes";
import { ProjectsBoardView } from "../ProjectsBoardView";
import { ProjectsGridView } from "../ProjectsGridView";
import { ProjectsListView } from "../ProjectsListView";
import visual from "../ProjectsScreen.module.css";
import { ProjectsEmptyState } from "./ProjectsEmptyState";

interface ProjectsSection2Props {
  filtered: E.Project[];
  t: (key: string, fallback?: string) => string;
  q: string;
  setDrawer: R.Dispatch<R.SetStateAction<E.ProjectDrawer | null>>;
  view: string;
  openMenu: (e: R.MouseEvent, project: E.Project) => void;
}

export function ProjectsSection2({
  filtered,
  t,
  q,
  setDrawer,
  view,
  openMenu,
}: ProjectsSection2Props) {
  return (
    <div className={visual.surface}>
      {filtered.length === 0 && <ProjectsEmptyState {...{ t: t, q: q, setDrawer: setDrawer }} />}
      {filtered.length > 0 && view === "list" && (
        <ProjectsListView
          projects={filtered}
          onOpen={(p) => {
            setDrawer({ mode: "view", project: p });
          }}
          onContextMenu={openMenu}
        />
      )}
      {filtered.length > 0 && view === "board" && (
        <ProjectsBoardView
          projects={filtered}
          onOpen={(p) => {
            setDrawer({ mode: "view", project: p });
          }}
          onContextMenu={openMenu}
        />
      )}
      {filtered.length > 0 && view === "grid" && (
        <ProjectsGridView
          projects={filtered}
          onOpen={(p) => {
            setDrawer({ mode: "view", project: p });
          }}
          onContextMenu={openMenu}
        />
      )}
    </div>
  );
}
