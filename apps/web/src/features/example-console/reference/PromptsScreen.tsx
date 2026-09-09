import { useState } from "react";
import FIX_PROMPTS from "../data/prompts.json";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import { Icon } from "./Icon";
import { PageToolbar } from "./PageToolbar";
import visual from "./PromptsScreen.module.css";
import { SearchInput } from "./SearchInput";
import { ViewSwitcher } from "./ViewSwitcher";
import { PromptsSection } from "./prompts-screen/PromptsSection";

export const PromptsScreen = () => {
  const { t } = useI18n();
  const [selectedId, setSelectedId] = useState("pr_01K5FZ8Q3");
  const [mode, setMode] = useState("editor"); // editor | ab
  const [q, setQ] = useState("");
  const selected = FIX_PROMPTS.find((p) => p.id === selectedId);
  const filtered = q
    ? FIX_PROMPTS.filter((p) => p.name.toLowerCase().includes(q.toLowerCase()))
    : FIX_PROMPTS;

  return (
    <div className={visual.column}>
      <PageToolbar title={t("pr.title")} subtitle={t("pr.subtitle")}>
        <SearchInput value={q} onChange={setQ} placeholder={t("pr.search")} width={220} />
        <ViewSwitcher
          value={mode}
          onChange={setMode}
          views={[
            { value: "editor", label: t("pr.viewEditor"), icon: "book" },
            { value: "ab", label: t("pr.viewAB"), icon: "fork" },
          ]}
        />
        <button className="btn primary sm">
          <Icon name="plus" size={11} /> {t("pr.new")}
        </button>
      </PageToolbar>

      <PromptsSection {...{ t, filtered, selectedId, setSelectedId, mode, selected }} />
    </div>
  );
};
