import { type Dispatch, type SetStateAction } from "react";
import { Icon } from "../Icon";
import { PageToolbar } from "../PageToolbar";
import { SearchInput } from "../SearchInput";
import { ViewSwitcher } from "../ViewSwitcher";

interface RunsHistoryTitleProps {
  t: (key: string, fallback?: string) => string;
  q: string;
  setQ: Dispatch<SetStateAction<string>>;
  view: string;
  setView: Dispatch<SetStateAction<string>>;
  selectedIds: string[];
}

export function RunsHistoryTitle({
  t,
  q,
  setQ,
  view,
  setView,
  selectedIds,
}: RunsHistoryTitleProps) {
  return (
    <PageToolbar title={t("rh.title")} subtitle={t("rh.subtitle")}>
      <SearchInput value={q} onChange={setQ} placeholder={t("rh.search")} width={220} />
      <ViewSwitcher
        value={view}
        onChange={setView}
        views={[
          { value: "list", label: t("rh.viewList"), icon: "menu" },
          { value: "diff", label: t("rh.viewDiff"), icon: "fork" },
        ]}
      />
      {view === "list" && (
        <button
          className="btn sm"
          disabled={selectedIds.length !== 2}
          onClick={() => {
            setView("diff");
          }}
        >
          <Icon name="fork" size={11} /> {t("rh.compare")} {selectedIds.length}/2
        </button>
      )}
    </PageToolbar>
  );
}
