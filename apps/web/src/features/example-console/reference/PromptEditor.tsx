import { useState } from "react";
import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import visual from "./PromptEditor.module.css";
import { PromptEditorMetric7d } from "./prompt-editor/PromptEditorMetric7d";
import { PromptEditorSection } from "./prompt-editor/PromptEditorSection";

export const PromptEditor = ({ prompt }: { prompt: E.Prompt }) => {
  const { t } = useI18n();
  const [tab, setTab] = useState("template");

  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <PromptEditorSection {...{ prompt, t, setTab, tab }} />

      <PromptEditorMetric7d {...{ tab, t, prompt }} />
    </div>
  );
};
