import { type Dispatch, type SetStateAction } from "react";
import type * as E from "../../exampleTypes";
import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../DatasetsScreen.module.css";
import { DatasetsRowsCol } from "./DatasetsRowsCol";
import { DatasetsSection } from "./DatasetsSection";
import { DatasetsSection7 } from "./DatasetsSection7";

interface DatasetsSection4Props {
  t: (key: string, fallback?: string) => string;
  filtered: FixtureTypes.Dataset[];
  selectedId: string;
  setSelectedId: Dispatch<SetStateAction<string>>;
  selected: FixtureTypes.Dataset | undefined;
  setTab: Dispatch<SetStateAction<string>>;
  tab: string;
  nodes: { id: string; label: string; group: string }[];
  edges: E.GraphEdge[];
}

export function DatasetsSection4({
  t,
  filtered,
  selectedId,
  setSelectedId,
  selected,
  setTab,
  tab,
  nodes,
  edges,
}: DatasetsSection4Props) {
  return (
    <div className={visual.grid}>
      <DatasetsSection {...{ t, filtered, selectedId, setSelectedId }} />

      {selected && (
        <div className={`panel ${visual.panel2 ?? ""}`}>
          <DatasetsSection7 {...{ t, selected, setTab, tab }} />

          <DatasetsRowsCol {...{ tab, t, selected, nodes, edges, setSelectedId }} />
        </div>
      )}
    </div>
  );
}
