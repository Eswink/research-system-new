import type * as R from "react";
import { useMemo, useState } from "react";
import FIX_PROJECTS from "../data/projects.json";
import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import visual from "./ProjectsScreen.module.css";
import { ProjectsContextMenu } from "./projects-screen/ProjectsContextMenu";
import { ProjectsDeleteConfirm } from "./projects-screen/ProjectsDeleteConfirm";
import { ProjectsDetailsDrawer } from "./projects-screen/ProjectsDetailsDrawer";
import { ProjectsSection } from "./projects-screen/ProjectsSection";
import { ProjectsSection2 } from "./projects-screen/ProjectsSection2";
import { ProjectsTitle } from "./projects-screen/ProjectsTitle";

function filterProjects(projects: E.Project[], statusFilter: string, query: string): E.Project[] {
  let list = projects;
  if (statusFilter !== "all") list = list.filter((project) => project.status === statusFilter);
  if (query.trim() === "") return list;
  const search = query.toLowerCase();
  return list.filter(
    (project) =>
      project.name.toLowerCase().includes(search) ||
      project.slug.toLowerCase().includes(search) ||
      project.tags.some((tag) => tag.toLowerCase().includes(search)),
  );
}

function projectCounts(projects: E.Project[]): Record<string, number> {
  const counts: Record<string, number> = { all: projects.length };
  projects.forEach((project) => {
    counts[project.status] = (counts[project.status] ?? 0) + 1;
  });
  return counts;
}

export const ProjectsScreen = () => {
  const { t } = useI18n();
  const [view, setView] = useState("list");
  const [q, setQ] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  // Drawer state is page-local and never persists project mutations.
  const [drawer, setDrawer] = useState<E.ProjectDrawer | null>(null);
  const [ctx, setCtx] = useState<{ x: number; y: number; project: E.Project } | null>(null); // menu
  const [confirmDelete, setConfirmDelete] = useState<E.Project | null>(null);
  const [projectsLocal, setProjectsLocal] = useState<E.Project[]>(FIX_PROJECTS);

  const filtered = useMemo(
    () => filterProjects(projectsLocal, statusFilter, q),
    [projectsLocal, statusFilter, q],
  );
  const counts = useMemo(() => projectCounts(projectsLocal), [projectsLocal]);

  const openMenu = (e: R.MouseEvent, project: E.Project) => {
    e.preventDefault();
    setCtx({ x: e.clientX, y: e.clientY, project });
  };

  return (
    <ProjectsScreenLayout
      {...{
        t,
        view,
        setView,
        q,
        setQ,
        statusFilter,
        setStatusFilter,
        drawer,
        setDrawer,
        ctx,
        setCtx,
        confirmDelete,
        setConfirmDelete,
        setProjectsLocal,
        filtered,
        counts,
        openMenu,
      }}
    />
  );
};

interface ProjectsScreenLayoutProps {
  t: (key: string, fallback?: string) => string;
  view: string;
  setView: R.Dispatch<R.SetStateAction<string>>;
  q: string;
  setQ: R.Dispatch<R.SetStateAction<string>>;
  statusFilter: string;
  setStatusFilter: R.Dispatch<R.SetStateAction<string>>;
  drawer: E.ProjectDrawer | null;
  setDrawer: R.Dispatch<R.SetStateAction<E.ProjectDrawer | null>>;
  ctx: { x: number; y: number; project: E.Project } | null;
  setCtx: R.Dispatch<R.SetStateAction<{ x: number; y: number; project: E.Project } | null>>;
  confirmDelete: E.Project | null;
  setConfirmDelete: R.Dispatch<R.SetStateAction<E.Project | null>>;
  setProjectsLocal: R.Dispatch<R.SetStateAction<E.Project[]>>;
  filtered: E.Project[];
  counts: Record<string, number>;
  openMenu: (event: R.MouseEvent, project: E.Project) => void;
}

function ProjectsScreenLayout(props: ProjectsScreenLayoutProps) {
  return (
    <div className={visual.column}>
      <ProjectsTitle
        t={props.t}
        q={props.q}
        setQ={props.setQ}
        view={props.view}
        setView={props.setView}
        setDrawer={props.setDrawer}
      />
      <ProjectsSection
        t={props.t}
        setStatusFilter={props.setStatusFilter}
        statusFilter={props.statusFilter}
        counts={props.counts}
      />
      <ProjectsSection2
        filtered={props.filtered}
        t={props.t}
        q={props.q}
        setDrawer={props.setDrawer}
        view={props.view}
        openMenu={props.openMenu}
      />
      <ProjectsDetailsDrawer
        drawer={props.drawer}
        setDrawer={props.setDrawer}
        t={props.t}
        setProjectsLocal={props.setProjectsLocal}
        setConfirmDelete={props.setConfirmDelete}
      />
      {props.ctx && (
        <ProjectsContextMenu
          ctx={props.ctx}
          setCtx={props.setCtx}
          t={props.t}
          setDrawer={props.setDrawer}
          setProjectsLocal={props.setProjectsLocal}
          setConfirmDelete={props.setConfirmDelete}
        />
      )}
      <ProjectsDeleteConfirm {...props} />
    </div>
  );
}
