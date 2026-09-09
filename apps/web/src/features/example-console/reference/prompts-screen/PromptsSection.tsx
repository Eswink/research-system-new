import { type Dispatch, type SetStateAction } from "react";
import type * as FixtureTypes from "../../fixtureTypes";
import { requiredExample } from "../../requiredExample";
import { PromptAB } from "../PromptAB";
import { PromptEditor } from "../PromptEditor";
import visual from "../PromptsScreen.module.css";
import { PromptsSection2 } from "./PromptsSection2";

interface PromptsSectionProps {
  t: (key: string, fallback?: string) => string;
  filtered: FixtureTypes.Prompt[];
  selectedId: string;
  setSelectedId: Dispatch<SetStateAction<string>>;
  mode: string;
  selected: FixtureTypes.Prompt | undefined;
}

export function PromptsSection({
  t,
  filtered,
  selectedId,
  setSelectedId,
  mode,
  selected,
}: PromptsSectionProps) {
  return (
    <div className={visual.grid}>
      {/* List */}
      <PromptsSection2 {...{ t, filtered, selectedId, setSelectedId }} />

      {mode === "editor" ? (
        <PromptEditor prompt={requiredExample(selected)} />
      ) : (
        <PromptAB prompt={requiredExample(selected)} />
      )}
    </div>
  );
}
