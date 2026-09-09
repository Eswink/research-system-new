import type * as R from "react";
import type * as E from "../../exampleTypes";
import { EmptyState } from "../EmptyState";

interface ProjectsEmptyStateProps {
  t: (key: string, fallback?: string) => string;
  q: string;
  setDrawer: R.Dispatch<R.SetStateAction<E.ProjectDrawer | null>>;
}

export function ProjectsEmptyState({ t, q, setDrawer }: ProjectsEmptyStateProps) {
  return (
    <EmptyState
      icon="hex"
      kicker={t("proj.emptyKicker")}
      title={q ? t("proj.emptyMatchTitle").replace("{q}", q) : t("proj.emptyFilterTitle")}
      description={q ? t("proj.emptyMatchDesc") : t("proj.emptyFilterDesc")}
      cta={{
        label: t("proj.new"),
        icon: "plus",
        onClick: () => {
          setDrawer({ mode: "create" });
        },
      }}
    />
  );
}
