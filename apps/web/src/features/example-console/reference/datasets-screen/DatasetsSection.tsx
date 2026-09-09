import { type Dispatch, type SetStateAction } from "react";
import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../DatasetsScreen.module.css";
import { DatasetsSection6 } from "./DatasetsSection6";

interface DatasetsSectionProps {
  t: (key: string, fallback?: string) => string;
  filtered: FixtureTypes.Dataset[];
  selectedId: string;
  setSelectedId: Dispatch<SetStateAction<string>>;
}

export function DatasetsSection({ t, filtered, selectedId, setSelectedId }: DatasetsSectionProps) {
  return (
    <div className={`panel ${visual.panel ?? ""}`}>
      <div className={`row head ${visual.surface ?? ""}`}>
        <span>{t("ds.colDataset")}</span>
        <span>{t("lbl.version")}</span>
        <span>{t("lbl.rows")}</span>
        <span>{t("lbl.size")}</span>
        <span>{t("lbl.format")}</span>
        <span>{t("lbl.schema")}</span>
      </div>
      <DatasetsSection6 {...{ filtered, selectedId, setSelectedId, t }} />
    </div>
  );
}
