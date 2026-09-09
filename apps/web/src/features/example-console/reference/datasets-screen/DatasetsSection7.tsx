import { type Dispatch, type SetStateAction } from "react";
import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../DatasetsScreen.module.css";
import { DigestText } from "../DigestText";

interface DatasetsSection7Props {
  t: (key: string, fallback?: string) => string;
  selected: FixtureTypes.Dataset;
  setTab: Dispatch<SetStateAction<string>>;
  tab: string;
}

export function DatasetsSection7({ t, selected, setTab, tab }: DatasetsSection7Props) {
  return (
    <div className={visual.surface5}>
      <div className={visual.row2}>
        <div className={visual.surface6}>
          <div className={visual.caption4}>
            {t("lbl.dataset")} · {selected.version}
          </div>
          <div className={visual.label5}>{selected.name}</div>
        </div>
        {selected.checksum && <DigestText value={selected.checksum} length={10} label="sha:" />}
      </div>
      <div className={visual.row3}>
        {(
          [
            ["preview", t("ds.tabPreview")],
            ["schema", t("ds.tabSchema")],
            ["lineage", t("ds.tabLineage")],
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
    </div>
  );
}
