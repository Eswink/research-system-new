import { type Dispatch, type SetStateAction } from "react";
import { Icon } from "../Icon";
import { PageToolbar } from "../PageToolbar";
import { ViewSwitcher } from "../ViewSwitcher";

interface LineageTitleProps {
  t: (key: string, fallback?: string) => string;
  filter: string;
  setFilter: Dispatch<SetStateAction<string>>;
}

export function LineageTitle({ t, filter, setFilter }: LineageTitleProps) {
  return (
    <PageToolbar title={t("ln.title")} subtitle={t("ln.subtitle")}>
      <ViewSwitcher
        value={filter}
        onChange={setFilter}
        views={[
          { value: "all", label: t("ln.filterAll") },
          { value: "upstream", label: t("ln.filterUp") },
          { value: "downstream", label: t("ln.filterDown") },
        ]}
      />
      <button className="btn sm">
        <Icon name="external" size={11} /> {t("ln.exportDot")}
      </button>
    </PageToolbar>
  );
}
