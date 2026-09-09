import { type Dispatch, type SetStateAction } from "react";
import visual from "../PromptEditor.module.css";

interface PromptEditorSection3Props {
  t: (key: string, fallback?: string) => string;
  setTab: Dispatch<SetStateAction<string>>;
  tab: string;
}

export function PromptEditorSection3({ t, setTab, tab }: PromptEditorSection3Props) {
  return (
    <div className={visual.row4}>
      {(
        [
          ["template", t("pr.tabTemplate")],
          ["variables", t("pr.tabVariables")],
          ["history", t("pr.tabHistory")],
          ["metrics", t("pr.tabMetrics")],
        ] as const
      ).map(([v, l]) => (
        <button
          key={v}
          onClick={() => {
            setTab(v);
          }}
          className="btn sm ghost"
          style={{
            background: tab === v ? "var(--bg-hover)" : "transparent",
            color: tab === v ? "var(--fg)" : "var(--fg-muted)",
            fontWeight: tab === v ? 500 : 400,
            borderColor: tab === v ? "var(--border-strong)" : "transparent",
          }}
        >
          {l}
        </button>
      ))}
    </div>
  );
}
