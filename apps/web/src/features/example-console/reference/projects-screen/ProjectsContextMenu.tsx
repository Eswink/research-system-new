import type * as R from "react";
import type * as E from "../../exampleTypes";
import { ContextMenu } from "../ContextMenu";

interface ProjectsContextMenuProps {
  ctx: { x: number; y: number; project: E.Project };
  setCtx: R.Dispatch<R.SetStateAction<{ x: number; y: number; project: E.Project } | null>>;
  t: (key: string, fallback?: string) => string;
  setDrawer: R.Dispatch<R.SetStateAction<E.ProjectDrawer | null>>;
  setProjectsLocal: R.Dispatch<R.SetStateAction<E.Project[]>>;
  setConfirmDelete: R.Dispatch<R.SetStateAction<E.Project | null>>;
}

function duplicateProject(
  setProjects: ProjectsContextMenuProps["setProjectsLocal"],
  project: E.Project,
): void {
  setProjects((previous) => [
    {
      ...project,
      id: `proj_dup_${crypto.randomUUID()}`,
      name: project.name + " (copy)",
      status: "DRAFT",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    ...previous,
  ]);
}

function archiveProject(
  setProjects: ProjectsContextMenuProps["setProjectsLocal"],
  project: E.Project,
): void {
  setProjects((previous) =>
    previous.map((entry) =>
      entry.id === project.id
        ? { ...entry, status: "ARCHIVED", archived_at: new Date().toISOString() }
        : entry,
    ),
  );
}

function projectMenuItems(props: ProjectsContextMenuProps): E.MenuItem[] {
  const { ctx, t, setDrawer, setProjectsLocal, setConfirmDelete } = props;
  return [
    {
      icon: "external",
      label: t("act.open"),
      shortcut: "O",
      action: () => {
        setDrawer({ mode: "view", project: ctx.project });
      },
    },
    {
      icon: "copy",
      label: t("act.edit"),
      shortcut: "E",
      action: () => {
        setDrawer({ mode: "edit", project: ctx.project });
      },
    },
    {
      icon: "fork",
      label: t("act.duplicate"),
      action: () => {
        duplicateProject(setProjectsLocal, ctx.project);
      },
    },
    { divider: true },
    {
      icon: "lock",
      label: t("act.archive"),
      action: () => {
        archiveProject(setProjectsLocal, ctx.project);
      },
    },
    {
      icon: "x",
      label: t("act.delete"),
      danger: true,
      action: () => {
        setConfirmDelete(ctx.project);
      },
    },
  ];
}

export function ProjectsContextMenu({
  ctx,
  setCtx,
  t,
  setDrawer,
  setProjectsLocal,
  setConfirmDelete,
}: ProjectsContextMenuProps) {
  const props = { ctx, setCtx, t, setDrawer, setProjectsLocal, setConfirmDelete };
  return (
    <ContextMenu
      x={ctx.x}
      y={ctx.y}
      onClose={() => {
        setCtx(null);
      }}
      items={projectMenuItems(props)}
    />
  );
}
