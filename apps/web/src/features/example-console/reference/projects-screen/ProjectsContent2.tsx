import type * as R from "react";
import type * as E from "../../exampleTypes";
import { Icon } from "../Icon";
import visual from "../ProjectsScreen.module.css";

interface ProjectsContent2Props {
  setDrawer: R.Dispatch<R.SetStateAction<E.ProjectDrawer | null>>;
  t: (key: string, fallback?: string) => string;
  drawer: E.ProjectDrawer | null;
}

export function ProjectsContent2({ setDrawer, t, drawer }: ProjectsContent2Props) {
  return (
    <>
      <button
        className="btn ghost"
        onClick={() => {
          setDrawer(null);
        }}
      >
        {t("act.cancel")}
      </button>
      <button
        className={`btn primary ${visual.action3 ?? ""}`}
        type="submit"
        form="example-project-draft"
      >
        <Icon name="check" size={11} />{" "}
        {drawer?.mode === "create" ? t("proj.createCta") : t("act.saveChanges")}
      </button>
    </>
  );
}
