import { type Dispatch, type SetStateAction } from "react";
import { Icon } from "../Icon";
import visual from "../NotebooksScreen.module.css";

interface NotebooksSection3Props {
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
}

export function NotebooksSection3({
  t,
  filtered,
  selectedId,
  setSelectedId,
}: NotebooksSection3Props) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={visual.row}>
        <Icon name="book" size={12} />
        <span className={visual.label}>{t("nb.notes")}</span>
        <span className="chip">{filtered.length}</span>
      </div>
      <div className={visual.surface}>
        {filtered.map((n) => {
          const active = n.id === selectedId;
          return (
            <div
              key={n.id}
              onClick={() => {
                setSelectedId(n.id);
              }}
              className={visual.surface2}
              style={{
                background: active ? "var(--bg-hover)" : "transparent",
                borderLeft: `2px solid ${active ? "var(--accent)" : "transparent"}`,
              }}
            >
              <div className={visual.label2}>{n.title}</div>
              <div className={visual.caption}>{n.excerpt}</div>
              <div className={visual.row2}>
                <span>{n.word_count}w</span>
                <span>·</span>
                <span>{new Date(n.updated_at).toISOString().slice(5, 10)}</span>
                {n.linked_claims.length > 0 && (
                  <span className={visual.surface3}>· {n.linked_claims.length}📎</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
