import { useMemo, useState } from "react";
import FIX_DATASETS from "../data/datasets.json";
import type * as E from "../exampleTypes";
import { useExampleI18n as useI18n } from "../useExampleI18n";
import visual from "./DatasetsScreen.module.css";
import { Icon } from "./Icon";
import { PageToolbar } from "./PageToolbar";
import { SearchInput } from "./SearchInput";
import { DatasetsNew } from "./datasets-screen/DatasetsNew";
import { DatasetsSection4 } from "./datasets-screen/DatasetsSection4";

export const DatasetsScreen = () => {
  const { t } = useI18n();
  const [selectedId, setSelectedId] = useState("ds_medqa_multi_v3");
  const [tab, setTab] = useState("preview");
  const [drawer, setDrawer] = useState<{ mode?: string } | null>(null);
  const [q, setQ] = useState("");
  const selected = FIX_DATASETS.find((d) => d.id === selectedId);
  const filtered = q
    ? FIX_DATASETS.filter((d) => d.name.toLowerCase().includes(q.toLowerCase()))
    : FIX_DATASETS;

  const { nodes, edges } = useMemo(buildDatasetGraph, []);

  return (
    <div className={visual.column}>
      <PageToolbar title={t("ds.title")} subtitle={t("ds.subtitle")}>
        <SearchInput value={q} onChange={setQ} placeholder={t("ds.search")} width={220} />
        <button className="btn sm" disabled title="EXAMPLE: file upload is unavailable">
          <Icon name="external" size={11} /> {t("ds.upload")}
        </button>
        <button
          className="btn primary sm"
          onClick={() => {
            setDrawer({ mode: "create" });
          }}
        >
          <Icon name="plus" size={11} /> {t("ds.new")}
        </button>
      </PageToolbar>

      <DatasetsSection4
        {...{ t, filtered, selectedId, setSelectedId, selected, setTab, tab, nodes, edges }}
      />

      <DatasetsNew {...{ drawer, setDrawer, t }} />
    </div>
  );
};

function buildDatasetGraph() {
  const nodes = FIX_DATASETS.map((dataset) => ({
    id: dataset.id,
    label: dataset.name.split(" ")[0] ?? dataset.name,
    group:
      dataset.lineage.parents.length === 0
        ? "root"
        : dataset.lineage.children.length === 0
          ? "leaf"
          : "mid",
  }));
  const edges: E.GraphEdge[] = [];
  FIX_DATASETS.forEach((dataset) => {
    dataset.lineage.children.forEach((child) => {
      edges.push({ from: dataset.id, to: child });
    });
  });
  return { nodes, edges };
}
