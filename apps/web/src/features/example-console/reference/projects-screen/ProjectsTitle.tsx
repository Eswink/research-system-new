import type * as R from "react";
import type * as E from "../../exampleTypes";
import { Icon } from "../Icon";
import { PageToolbar } from "../PageToolbar";
import { SearchInput } from "../SearchInput";
import { ViewSwitcher } from "../ViewSwitcher";

interface ProjectsTitleProps {
  t: (key: string, fallback?: string) => string;
  q: string;
  setQ: R.Dispatch<R.SetStateAction<string>>;
  view: string;
  setView: R.Dispatch<R.SetStateAction<string>>;
  setDrawer: R.Dispatch<R.SetStateAction<E.ProjectDrawer | null>>;
}

export function ProjectsTitle({ t, q, setQ, view, setView, setDrawer }: ProjectsTitleProps) {
  return (
    <PageToolbar title={t("proj.title")} subtitle={t("proj.subtitle")}>
      <SearchInput value={q} onChange={setQ} placeholder={t("proj.search")} width={240} />
      <ViewSwitcher
        value={view}
        onChange={setView}
        views={[
          { value: "list", label: t("proj.viewList"), icon: "menu" },
          { value: "board", label: t("proj.viewBoard"), icon: "hex" },
          { value: "grid", label: t("proj.viewGrid"), icon: "square" },
        ]}
      />
      <button
        className="btn primary sm"
        onClick={() => {
          setDrawer({ mode: "create" });
        }}
      >
        <Icon name="plus" size={11} /> {t("proj.new")}
      </button>
    </PageToolbar>
  );
}
