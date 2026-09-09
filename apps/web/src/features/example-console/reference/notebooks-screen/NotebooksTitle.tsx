import { type Dispatch, type SetStateAction } from "react";
import { Icon } from "../Icon";
import visual from "../NotebooksScreen.module.css";
import { PageToolbar } from "../PageToolbar";
import { SearchInput } from "../SearchInput";
import { NotebooksNew } from "./NotebooksNew";
import { NotebooksSection } from "./NotebooksSection";

interface NotebooksTitleProps {
  t: (key: string, fallback?: string) => string;
  q: string;
  setQ: Dispatch<SetStateAction<string>>;
  setDrawer: Dispatch<SetStateAction<{ mode?: string } | null>>;
  filtered: {
    id: string;
    title: string;
    author: string;
    updated_at: string;
    word_count: number;
    linked_claims: string[];
    linked_runs: string[];
    excerpt: string;
  }[];
  selectedId: string;
  setSelectedId: Dispatch<SetStateAction<string>>;
  selected:
    | {
        id: string;
        title: string;
        author: string;
        updated_at: string;
        word_count: number;
        linked_claims: string[];
        linked_runs: string[];
        excerpt: string;
      }
    | undefined;
  drawer: { mode?: string } | null;
}

export function NotebooksTitle({
  t,
  q,
  setQ,
  setDrawer,
  filtered,
  selectedId,
  setSelectedId,
  selected,
  drawer,
}: NotebooksTitleProps) {
  return (
    <div className={visual.column}>
      <PageToolbar title={t("nb.title")} subtitle={t("nb.subtitle")}>
        <SearchInput value={q} onChange={setQ} placeholder={t("nb.search")} width={220} />
        <button
          className="btn primary sm"
          onClick={() => {
            setDrawer({});
          }}
        >
          <Icon name="plus" size={11} /> {t("nb.new")}
        </button>
      </PageToolbar>

      <NotebooksSection {...{ t, filtered, selectedId, setSelectedId, selected }} />

      <NotebooksNew {...{ drawer, setDrawer, t }} />
    </div>
  );
}
