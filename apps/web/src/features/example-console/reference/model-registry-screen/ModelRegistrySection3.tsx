import { type Dispatch, type SetStateAction } from "react";
import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../ModelRegistryScreen.module.css";
import { ModelRegistrySection5 } from "./ModelRegistrySection5";

interface ModelRegistrySection3Props {
  cols: string;
  t: (key: string, fallback?: string) => string;
  filtered: FixtureTypes.RegisteredModel[];
  selectedId: string;
  setSelectedId: Dispatch<SetStateAction<string>>;
}

export function ModelRegistrySection3({
  cols,
  t,
  filtered,
  selectedId,
  setSelectedId,
}: ModelRegistrySection3Props) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className="row head" style={{ gridTemplateColumns: cols }}>
        <span>{t("mr.col.model")}</span>
        <span>{t("mr.col.provider")}</span>
        <span>{t("mr.col.family")}</span>
        <span>{t("mr.col.context")}</span>
        <span>{t("mr.col.license")}</span>
      </div>
      <ModelRegistrySection5 {...{ filtered, selectedId, setSelectedId, cols }} />
    </div>
  );
}
