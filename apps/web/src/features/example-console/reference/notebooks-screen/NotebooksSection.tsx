import { type Dispatch, type SetStateAction } from "react";
import { Icon } from "../Icon";
import visual from "../NotebooksScreen.module.css";
import { NotebooksSection2 } from "./NotebooksSection2";
import { NotebooksSection3 } from "./NotebooksSection3";

interface NotebooksSectionProps {
  t: (key: string, fallback?: string) => string;
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
}

export function NotebooksSection({
  t,
  filtered,
  selectedId,
  setSelectedId,
  selected,
}: NotebooksSectionProps) {
  return (
    <div className={visual.grid}>
      <NotebooksSection3 {...{ t, filtered, selectedId, setSelectedId }} />

      {selected && (
        <div className={`panel ${visual.panel2 ?? ""}`}>
          <div className={visual.surface4}>
            <div className={visual.row3}>
              <div className={visual.surface5}>
                <div className={visual.caption2}>
                  {new Date(selected.updated_at).toISOString().replace("T", " ").slice(0, 16)}
                  {" · "}
                  {selected.author}
                </div>
                <div className={visual.label3}>{selected.title}</div>
              </div>
              <button className="btn sm">
                <Icon name="copy" size={10} /> {t("act.edit")}
              </button>
            </div>
          </div>

          <NotebooksSection2 {...{ selected, t }} />
        </div>
      )}
    </div>
  );
}
