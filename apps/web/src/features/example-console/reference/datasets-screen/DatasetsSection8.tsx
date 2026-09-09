import { type Dispatch, type SetStateAction } from "react";
import FIX_DATASETS from "../../data/datasets.json";
import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../DatasetsScreen.module.css";
import { Icon } from "../Icon";

interface DatasetsSection8Props {
  t: (key: string, fallback?: string) => string;
  selected: FixtureTypes.Dataset;
  setSelectedId: Dispatch<SetStateAction<string>>;
}

export function DatasetsSection8({ t, selected, setSelectedId }: DatasetsSection8Props) {
  return (
    <div>
      <div className={visual.caption10}>
        {t("ds.parents")} ({selected.lineage.parents.length})
      </div>
      {selected.lineage.parents.length === 0 ? (
        <span className="empty-mark">{t("ds.noParents")}</span>
      ) : (
        selected.lineage.parents.map((p) => {
          const parent = FIX_DATASETS.find((d) => d.id === p);
          return parent ? (
            <div
              key={p}
              className={visual.label8}
              onClick={() => {
                setSelectedId(p);
              }}
            >
              <Icon name="chevron-r" size={8} className={visual.surface20} />{" "}
              <span className={`mono ${visual.surface21 ?? ""}`}>{parent.name}</span>
            </div>
          ) : null;
        })
      )}
    </div>
  );
}
