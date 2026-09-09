import type { Dispatch, SetStateAction } from "react";
import type { Project, ProjectDrawer } from "../../exampleTypes";
import { Drawer } from "../Drawer";
import { ProjectDetail } from "../ProjectDetail";
import { ProjectForm } from "../ProjectForm";
import { ProjectsContent } from "./ProjectsContent";
import { ProjectsContent2 } from "./ProjectsContent2";

interface Props {
  drawer: ProjectDrawer | null;
  setDrawer: Dispatch<SetStateAction<ProjectDrawer | null>>;
  t: (key: string, fallback?: string) => string;
  setProjectsLocal: Dispatch<SetStateAction<Project[]>>;
  setConfirmDelete: Dispatch<SetStateAction<Project | null>>;
}

export function ProjectsDetailsDrawer(props: Props) {
  const { drawer, setDrawer, t, setProjectsLocal } = props;
  if (drawer === null) return null;
  const viewing = drawer.mode === "view";
  const title = viewing
    ? drawer.project.name
    : t(drawer.mode === "create" ? "proj.createTitle" : "proj.editTitle");
  const subtitle = t(
    viewing
      ? "proj.detailSubtitle"
      : drawer.mode === "create"
        ? "proj.createSubtitle"
        : "proj.editSubtitle",
  );
  const save = (project: Project) => {
    setProjectsLocal((items) =>
      drawer.mode === "create"
        ? [...items, project]
        : items.map((item) => (item.id === project.id ? project : item)),
    );
    setDrawer({ mode: "view", project });
  };
  return (
    <Drawer
      open
      onClose={() => {
        setDrawer(null);
      }}
      title={title}
      subtitle={subtitle}
      width={viewing ? 560 : 480}
      footer={
        viewing ? (
          <ProjectsContent {...props} drawer={drawer} />
        ) : (
          <ProjectsContent2 setDrawer={setDrawer} t={t} drawer={drawer} />
        )
      }
    >
      {viewing ? (
        <ProjectDetail project={drawer.project} />
      ) : (
        <ProjectForm key={drawer.project?.id ?? "create"} project={drawer.project} onSave={save} />
      )}
    </Drawer>
  );
}
