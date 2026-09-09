import { type Dispatch, type SetStateAction } from "react";
import type * as FixtureTypes from "../../fixtureTypes";
import { Icon } from "../Icon";
import visual from "../ModelRegistryScreen.module.css";
import { ModelRegistrySection } from "./ModelRegistrySection";
import { ModelRegistrySection3 } from "./ModelRegistrySection3";

interface ModelRegistrySection2Props {
  cols: string;
  t: (key: string, fallback?: string) => string;
  filtered: FixtureTypes.RegisteredModel[];
  selectedId: string;
  setSelectedId: Dispatch<SetStateAction<string>>;
  selected: FixtureTypes.RegisteredModel | undefined;
}

export function ModelRegistrySection2({
  cols,
  t,
  filtered,
  selectedId,
  setSelectedId,
  selected,
}: ModelRegistrySection2Props) {
  return (
    <div className={visual.grid}>
      <ModelRegistrySection3 {...{ cols, t, filtered, selectedId, setSelectedId }} />

      {selected && (
        <div className={`panel ${visual.panel2 ?? ""}`}>
          <div className={visual.surface4}>
            <div className={visual.caption6}>
              {selected.provider} · {selected.released}
            </div>
            <div className={visual.label3}>{selected.family}</div>
            <div className={visual.row2}>
              {selected.tags.map((tag) => (
                <span key={tag} className={`chip ${visual.surface5 ?? ""}`}>
                  {tag}
                </span>
              ))}
            </div>
            {selected.warning && (
              <div className={visual.row3}>
                <Icon name="warn-tri" size={12} /> {selected.warning}
              </div>
            )}
          </div>
          <ModelRegistrySection {...{ t, selected }} />
        </div>
      )}
    </div>
  );
}
