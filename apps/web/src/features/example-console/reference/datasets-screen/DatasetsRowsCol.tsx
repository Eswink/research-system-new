import { type Dispatch, type SetStateAction } from "react";
import type * as E from "../../exampleTypes";
import type * as FixtureTypes from "../../fixtureTypes";
import visual from "../DatasetsScreen.module.css";
import { Icon } from "../Icon";
import { MetricCard } from "../MetricCard";
import { DatasetsSection2 } from "./DatasetsSection2";
import { DatasetsSection3 } from "./DatasetsSection3";
import { DatasetsSection5 } from "./DatasetsSection5";

interface DatasetsRowsColProps {
  tab: string;
  t: (key: string, fallback?: string) => string;
  selected: FixtureTypes.Dataset;
  nodes: { id: string; label: string; group: string }[];
  edges: E.GraphEdge[];
  setSelectedId: Dispatch<SetStateAction<string>>;
}

const DATASET_SCHEMA = [
  ["id", "string", "unique row id"],
  ["language", "enum[en,es,zh,ar,pt,fr,de]", "target language"],
  ["question", "string", "clinical query"],
  ["gold_answer", "string", "clinician-verified answer"],
  ["model_output", "string", "model response"],
  ["dose_mg", "float?", "extracted dose in mg (nullable)"],
  ["source_doi", "string", "PubMed / WHO reference"],
] as const;

export function DatasetsRowsCol({
  tab,
  t,
  selected,
  nodes,
  edges,
  setSelectedId,
}: DatasetsRowsColProps) {
  return (
    <div className={visual.surface7}>
      {tab === "preview" && <DatasetPreview {...{ t, selected }} />}
      {tab === "schema" && <DatasetSchema {...{ t, selected }} />}
      {tab === "lineage" && <DatasetLineage {...{ t, selected, nodes, edges, setSelectedId }} />}
    </div>
  );
}

function DatasetPreview({ t, selected }: Pick<DatasetsRowsColProps, "t" | "selected">) {
  return (
    <div>
      <div className={visual.grid2}>
        <MetricCard label={t("ds.rowsCol")} value={selected.rows?.toLocaleString() ?? "—"} />
        <MetricCard label={t("ds.columnsCol")} value={selected.columns ?? "—"} />
      </div>
      <div className={visual.caption5}>{t("ds.sampleRows")}</div>
      <DatasetsSection2 {...{}} />
      <div className={visual.caption7}>
        {t("ds.showingRows").replace("{n}", selected.rows?.toLocaleString() ?? "?")}
      </div>
    </div>
  );
}

function DatasetSchema({ t, selected }: Pick<DatasetsRowsColProps, "t" | "selected">) {
  return (
    <div>
      {selected.schema_valid === false && selected.schema_errors && (
        <div className={visual.surface13}>
          <div className={visual.row4}>
            <Icon name="x" size={11} className={visual.surface14} />
            <span className={visual.label6}>
              {selected.schema_errors.length} {t("ds.schemaErrors")}
            </span>
          </div>
          {selected.schema_errors.map((error, index) => (
            <div key={index} className={visual.label7}>
              <span className={`mono ${visual.surface15 ?? ""}`}>{error.column}</span>:{" "}
              {error.issue}
            </div>
          ))}
        </div>
      )}
      <div className={visual.caption8}>{t("ds.columnSchema")}</div>
      {DATASET_SCHEMA.map(([column, type, description]) => (
        <div key={column} className={visual.grid3}>
          <span className={`mono ${visual.surface16 ?? ""}`}>{column}</span>
          <span className={`mono ${visual.surface17 ?? ""}`}>{type}</span>
          <span className={visual.surface18}>{description}</span>
        </div>
      ))}
    </div>
  );
}

function DatasetLineage({
  t,
  selected,
  nodes,
  edges,
  setSelectedId,
}: Omit<DatasetsRowsColProps, "tab">) {
  return (
    <div>
      <div className={visual.caption9}>
        {t("ds.dataLineage")} · {selected.name}
      </div>
      <DatasetsSection5 {...{ nodes, edges }} />
      <DatasetsSection3 {...{ t, selected, setSelectedId }} />
    </div>
  );
}
