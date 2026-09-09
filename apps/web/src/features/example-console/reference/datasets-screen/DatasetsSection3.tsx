import { type Dispatch, type SetStateAction } from "react";
import FIX_DATASETS from "../../data/datasets.json";
import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../DatasetsScreen.module.css";
import { Icon } from "../Icon";
import { DatasetsSection8 } from "./DatasetsSection8";

interface DatasetsSection3Props {
  t: (key: string, fallback?: string) => string;
  selected: FixtureTypes.Dataset;
  setSelectedId: Dispatch<SetStateAction<string>>;
}

export function DatasetsSection3({ t, selected, setSelectedId }: DatasetsSection3Props) {
  return (
    <div className={visual.grid4}>
      <DatasetsSection8 {...{ t, selected, setSelectedId }} />
      <div>
        <div className={visual.caption11}>
          {t("ds.children")} ({selected.lineage.children.length})
        </div>
        {selected.lineage.children.length === 0 ? (
          <span className="empty-mark">{t("ds.noChildren")}</span>
        ) : (
          selected.lineage.children.map((p) => {
            const child = FIX_DATASETS.find((d) => d.id === p);
            return child ? (
              <div
                key={p}
                className={visual.label9}
                onClick={() => {
                  setSelectedId(p);
                }}
              >
                <Icon name="chevron-r" size={8} className={visual.surface22} />{" "}
                <span className={`mono ${visual.surface23 ?? ""}`}>{child.name}</span>
              </div>
            ) : null;
          })
        )}
      </div>
    </div>
  );
}
